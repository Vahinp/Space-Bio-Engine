# chat.py
"""
Chat module: REST + WebSocket (Socket.IO) with a small SQLite store.
- NEW: If a thread is type="ai", posting a user message will trigger an AI reply
       using an app-configured AI_REPLY_FN(thread, recent_messages) -> dict
"""

from datetime import datetime
from typing import Optional, List, Dict, Any

from flask import Blueprint, request, jsonify, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, join_room, emit

# --- Globals for init_app pattern ---
db = SQLAlchemy()
socketio = SocketIO(cors_allowed_origins=["http://localhost:3000", "http://127.0.0.1:3000"])

# --- Models ---
class Thread(db.Model):
    __tablename__ = "threads"
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(16), nullable=False, default="dm")  # dm, group, ai
    title = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Message(db.Model):
    __tablename__ = "messages"
    id = db.Column(db.Integer, primary_key=True)
    thread_id = db.Column(db.Integer, db.ForeignKey("threads.id", ondelete="CASCADE"), index=True, nullable=False)
    sender = db.Column(db.String(128), nullable=True)   # store username/email/string
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    thread = db.relationship("Thread", backref="messages")


# --- Blueprint ---
chat_bp = Blueprint("chat", __name__, url_prefix="/api/chat")


def _serialize_message(m: Message) -> Dict[str, Any]:
    return {
        "id": m.id,
        "thread_id": m.thread_id,
        "sender": m.sender,
        "content": m.content,
        "created_at": m.created_at.isoformat()
    }


@chat_bp.route("/threads", methods=["POST"])
def create_thread():
    """
    body: { "type": "dm" | "group" | "ai", "title": "optional" }
    returns: {id, type, title, created_at}
    """
    data = request.get_json(force=True) or {}
    t = Thread(type=data.get("type", "dm"), title=data.get("title"))
    db.session.add(t)
    db.session.commit()
    return jsonify({"id": t.id, "type": t.type, "title": t.title, "created_at": t.created_at.isoformat()}), 201


@chat_bp.route("/threads/<int:thread_id>/messages", methods=["GET"])
def list_messages(thread_id: int):
    """
    query: ?before=<iso8601>&limit=50
    """
    limit = max(1, min(int(request.args.get("limit", 50)), 200))
    before: Optional[str] = request.args.get("before")

    q = Message.query.filter_by(thread_id=thread_id).order_by(Message.created_at.desc())
    if before:
        try:
            dt = datetime.fromisoformat(before.replace("Z", "+00:00"))
            q = q.filter(Message.created_at < dt)
        except Exception:
            pass

    msgs = q.limit(limit).all()
    # return newest-last for UI
    msgs = list(reversed(msgs))
    return jsonify([_serialize_message(m) for m in msgs])


def _maybe_ai_reply(thread: Thread, user_msg: Message):
    """
    If thread is AI, call configured AI reply function synchronously and emit.
    """
    if thread.type != "ai":
        return

    ai_fn = current_app.config.get("AI_REPLY_FN")
    if not ai_fn:
        return

    # Gather recent messages (last 20)
    recent: List[Message] = (
        Message.query.filter_by(thread_id=thread.id)
        .order_by(Message.created_at.desc()).limit(20).all()
    )
    recent = list(reversed(recent))

    try:
        result = ai_fn(thread, recent)  # expected: {"role":"assistant","content":"...","sources":[...]}
        content = (result or {}).get("content", "").strip()
        if not content:
            return
        # Save the assistant message
        assistant_msg = Message(thread_id=thread.id, sender="assistant", content=content[:4000])
        db.session.add(assistant_msg)
        db.session.commit()

        payload = _serialize_message(assistant_msg)
        # Also include sources if present (client can show them)
        if "sources" in (result or {}):
            payload["sources"] = result["sources"]

        socketio.emit("message:created", payload, room=f"thread:{thread.id}")
    except Exception as e:
        # emit a lightweight error assistant message
        err_msg = Message(thread_id=thread.id, sender="assistant",
                          content=f"Sorry—AI reply failed: {e}")
        db.session.add(err_msg)
        db.session.commit()
        socketio.emit("message:created", _serialize_message(err_msg), room=f"thread:{thread.id}")


@chat_bp.route("/threads/<int:thread_id>/messages", methods=["POST"])
def post_message(thread_id: int):
    """
    body: { "content": "...", "sender": "optional-identifier" }
    Also emits 'message:created' to websocket room "thread:<id>"
    Triggers AI reply if thread.type == "ai" and sender != "assistant"
    """
    data = request.get_json(force=True) or {}
    content = (data.get("content") or "").strip()
    if not content:
        return {"error": "content required"}, 400

    sender = (data.get("sender") or "user")
    t: Optional[Thread] = Thread.query.get(thread_id)
    if not t:
        return {"error": "thread not found"}, 404

    msg = Message(thread_id=thread_id, sender=sender, content=content[:4000])
    db.session.add(msg)
    db.session.commit()

    payload = _serialize_message(msg)
    socketio.emit("message:created", payload, room=f"thread:{thread_id}")

    # AI auto-reply (sync)
    if sender != "assistant":
        _maybe_ai_reply(t, msg)

    return jsonify(payload), 201


# --- Socket.IO events ---
@socketio.on("join")
def on_join(data):
    """
    client emits: socket.emit('join', { threadId });
    """
    try:
        thread_id = int(data.get("threadId"))
    except Exception:
        return
    if not Thread.query.get(thread_id):
        return
    join_room(f"thread:{thread_id}")
    emit("presence:joined", {"threadId": thread_id})


@socketio.on("message:new")
def on_message_new(data):
    """
    Alternative path to post via socket:
    client emits: socket.emit('message:new', { threadId, content, sender })
    """
    try:
        thread_id = int(data.get("threadId"))
    except Exception:
        return
    t: Optional[Thread] = Thread.query.get(thread_id)
    if not t:
        return

    content = (data.get("content") or "").strip()
    sender = (data.get("sender") or "user")
    if not content:
        return

    msg = Message(thread_id=thread_id, sender=sender, content=content[:4000])
    db.session.add(msg)
    db.session.commit()

    payload = _serialize_message(msg)
    emit("message:created", payload, room=f"thread:{thread_id}")

    if sender != "assistant":
        _maybe_ai_reply(t, msg)


def init_chat(app):
    """
    Call from your app factory.
    - configures SQLite for chat
    - registers blueprint
    - returns the socketio instance for running the app
    """
    app.config.setdefault("SQLALCHEMY_DATABASE_URI", "sqlite:///chat.db")
    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)

    db.init_app(app)
    with app.app_context():
        db.create_all()

    app.register_blueprint(chat_bp)
    socketio.init_app(app)
    return socketio
