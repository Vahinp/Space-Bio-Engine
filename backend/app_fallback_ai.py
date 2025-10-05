#!/usr/bin/env python3

import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from database import get_papers
from elasticsearch_service import ElasticsearchService

app = Flask(__name__)
CORS(app)

# Initialize Elasticsearch service
es_service = ElasticsearchService()

@app.route('/')
def home():
    return jsonify({
        "message": "NASA Bio-Exploration Dashboard API with Fallback AI",
        "version": "2.0-fallback",
        "endpoints": {
            "papers": "/api/papers",
            "search": "/api/search",
            "chat": "/api/chat",
            "chat/context": "/api/chat/context"
        }
    })

@app.route('/api/papers')
def get_all_papers():
    """Get all papers from database"""
    try:
        papers = get_papers(limit=1000, offset=0)  # Get up to 1000 papers
        return jsonify({
            "papers": papers,
            "total": len(papers)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/search', methods=['POST'])
def search_papers():
    """Search papers using Elasticsearch"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        filters = data.get('filters', {})
        
        # Use Elasticsearch service for search
        results = es_service.search_papers(query, filters)
        
        return jsonify({
            "papers": results.get('papers', []),
            "total": results.get('total', 0),
            "query": query
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat_fallback():
    """Fallback chat without Azure OpenAI"""
    try:
        data = request.get_json()
        messages = data.get('messages', [])
        
        if not messages:
            return jsonify({"error": "No messages provided"}), 400
        
        # Get the last user message
        last_message = messages[-1] if messages else {"content": "Hello"}
        user_question = last_message.get('content', 'Hello')
        
        # Simple keyword-based responses
        responses = {
            "microgravity": "Microgravity affects bone density, muscle mass, and cardiovascular function. Research shows astronauts lose 1-2% bone density per month in space.",
            "radiation": "Space radiation exposure is a major concern for long-duration missions. Studies focus on shielding and biological countermeasures.",
            "bone": "Bone loss in space occurs primarily in weight-bearing bones. Exercise countermeasures can reduce but not eliminate this loss.",
            "muscle": "Muscle atrophy in space affects both skeletal and cardiac muscle. Resistance exercise is the primary countermeasure.",
            "immune": "Spaceflight affects immune system function, with studies showing changes in T-cell function and cytokine production.",
            "plant": "Plant growth in space is studied for life support systems. Microgravity affects root orientation and nutrient uptake.",
            "cell": "Cell behavior changes in microgravity, affecting gene expression, protein synthesis, and cellular communication."
        }
        
        # Find relevant response based on keywords
        answer = "Based on the NASA Bio-Exploration database, "
        found_keyword = False
        
        for keyword, response in responses.items():
            if keyword.lower() in user_question.lower():
                answer += response
                found_keyword = True
                break
        
        if not found_keyword:
            answer += "I can help you explore space biology research topics including microgravity effects, radiation exposure, bone and muscle changes, immune system responses, plant growth, and cellular behavior. What specific area interests you?"
        
        return jsonify({
            "answer": answer,
            "fallback": True,
            "usage": {"total_tokens": 50}
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/chat/context', methods=['POST'])
def chat_with_context_fallback():
    """Fallback context-aware chat"""
    try:
        data = request.get_json()
        messages = data.get('messages', [])
        search_query = data.get('searchQuery', '')
        
        # Get relevant papers for context
        context_papers = []
        if search_query:
            try:
                search_results = es_service.search_papers(search_query, {})
                context_papers = search_results.get('papers', [])[:3]  # Top 3 papers
            except:
                pass
        
        # Get the last user message
        last_message = messages[-1] if messages else {"content": "Hello"}
        user_question = last_message.get('content', 'Hello')
        
        # Create context from papers
        context = ""
        if context_papers:
            context = "Based on the research papers in the database:\n\n"
            for i, paper in enumerate(context_papers, 1):
                context += f"{i}. {paper.get('title', 'Unknown Title')}\n"
                if paper.get('abstract'):
                    context += f"   {paper.get('abstract', '')[:200]}...\n\n"
        
        # Enhanced responses with context and more detailed information
        if "microgravity" in user_question.lower() or "bone" in user_question.lower():
            answer = f"""{context}Microgravity significantly impacts bone density and muscle mass. Key findings from space biology research:

• **Bone Density Loss**: Astronauts experience 1-2% bone density loss per month, primarily in weight-bearing bones (spine, hips, legs)
• **Mechanisms**: Reduced mechanical loading, altered calcium metabolism, and changes in bone remodeling processes
• **Countermeasures**: Advanced Resistive Exercise Device (ARED) can reduce bone loss by ~40%
• **Recovery**: Post-flight recovery typically takes 6-12 months depending on mission duration

This research is critical for planning long-duration missions beyond low Earth orbit."""
            
        elif "radiation" in user_question.lower():
            answer = f"""{context}Space radiation is a critical concern for long-duration missions. Current research focuses on:

• **Risk Assessment**: Galactic cosmic rays and solar particle events pose significant health risks
• **Shielding Technologies**: Advanced materials and magnetic shielding concepts
• **Biological Countermeasures**: Antioxidants, radioprotective compounds, and genetic factors
• **Monitoring**: Real-time dosimetry and biological markers for radiation exposure

Understanding radiation effects is essential for Mars missions and deep space exploration."""
            
        elif "immune" in user_question.lower():
            answer = f"""{context}Spaceflight affects immune system function in multiple ways:

• **T-cell Changes**: Reduced T-cell proliferation and altered cytokine production
• **Stress Response**: Elevated cortisol and stress hormones affect immune function
• **Microbiome**: Changes in gut microbiota composition during spaceflight
• **Countermeasures**: Exercise, nutrition, and stress management protocols

These findings are crucial for maintaining astronaut health during extended missions."""
            
        elif "plant" in user_question.lower() or "crop" in user_question.lower():
            answer = f"""{context}Plant growth in space is essential for life support systems and food production:

• **Root Orientation**: Microgravity affects root growth patterns and nutrient uptake
• **Light Requirements**: LED systems optimized for space agriculture
• **Water Management**: Hydroponic and aeroponic systems for zero-gravity
• **Crop Selection**: Fast-growing, nutrient-dense plants for space missions

Research focuses on sustainable food production for long-duration space missions."""
            
        elif "muscle" in user_question.lower() or "atrophy" in user_question.lower():
            answer = f"""{context}Muscle atrophy in space affects both skeletal and cardiac muscle:

• **Rate of Loss**: 1-2% muscle mass loss per month in space
• **Muscle Groups**: Type I (slow-twitch) fibers most affected
• **Countermeasures**: Resistance exercise, electrical stimulation, nutritional interventions
• **Recovery**: Exercise protocols can reduce but not eliminate muscle loss

Understanding muscle changes is vital for astronaut health and mission success."""
            
        else:
            answer = f"""{context}I can help you explore various aspects of space biology research. The NASA Bio-Exploration database contains research on:

• **Microgravity Effects**: Bone density, muscle atrophy, cardiovascular changes
• **Radiation Exposure**: Health risks, shielding, biological countermeasures  
• **Immune System**: T-cell function, stress responses, microbiome changes
• **Plant Biology**: Crop growth, life support systems, space agriculture
• **Cellular Biology**: Gene expression, protein synthesis, cellular communication

What specific area of space biology research interests you most?"""
        
        return jsonify({
            "answer": answer,
            "context_papers": len(context_papers),
            "fallback": True,
            "usage": {"total_tokens": 100}
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("🚀 Starting NASA Bio-Exploration Dashboard API with Fallback AI...")
    print("📝 Note: Using fallback responses (Azure OpenAI not configured)")
    app.run(debug=True, port=5001)
