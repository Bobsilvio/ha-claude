"""Blueprint registration for Flask routes."""

from flask import Flask
from routes.chat_routes import chat_bp
from routes.agents_routes import agents_bp
from routes.mcp_routes import mcp_bp
from routes.memory_routes import memory_bp
from routes.document_routes import document_bp
from routes.conversation_routes import conversation_bp
from routes.settings_routes import settings_bp
from routes.voice_routes import voice_bp
from routes.messaging_routes import messaging_bp
from routes.oauth_routes import oauth_bp
from routes.nvidia_routes import nvidia_bp
from routes.catalog_routes import catalog_bp
from routes.analytics_routes import analytics_bp
from routes.ui_routes import ui_bp
from routes.bubble_routes import bubble_bp
from routes.legacy_routes import legacy_bp
from routes.system_routes import system_bp
from routes.usage_routes import usage_bp
from routes.dashboard_routes import dashboard_bp
from routes.file_routes import file_bp
from routes.scheduled_routes import scheduled_bp


# Mapping of blueprint areas to route definitions
# Each entry is (blueprint_object, url, endpoint_name, methods)
ROUTE_REGISTRATIONS = {
    'chat': [
        (chat_bp, '/api/chat', 'api_chat', ['POST']),
        (chat_bp, '/api/chat/stream', 'api_chat_stream', ['POST']),
        (chat_bp, '/api/chat/abort', 'api_chat_abort', ['POST']),
        (chat_bp, '/api/memory/clear', 'api_memory_clear', ['POST']),
    ],
    'agents': [
        (agents_bp, '/api/agents', 'api_agents_list', ['GET']),
        (agents_bp, '/api/agents', 'api_agents_create', ['POST']),
        (agents_bp, '/api/agents/<agent_id>', 'api_agents_get', ['GET']),
        (agents_bp, '/api/agents/<agent_id>', 'api_agents_update', ['PUT']),
        (agents_bp, '/api/agents/<agent_id>', 'api_agents_delete', ['DELETE']),
        (agents_bp, '/api/agents/set', 'api_agents_set', ['POST']),
        (agents_bp, '/api/agents/channels', 'api_agents_channels_get', ['GET']),
        (agents_bp, '/api/agents/channels', 'api_agents_channels_put', ['PUT']),
        (agents_bp, '/api/agents/defaults', 'api_agents_defaults_get', ['GET']),
        (agents_bp, '/api/agents/defaults', 'api_agents_defaults_put', ['PUT']),
    ],
    'mcp': [
        (mcp_bp, '/api/mcp/servers', 'api_mcp_servers', ['GET']),
        (mcp_bp, '/api/mcp/server/<server_name>/status', 'api_mcp_server_status', ['GET']),
        (mcp_bp, '/api/mcp/server/<server_name>/reconnect', 'api_mcp_server_reconnect', ['POST']),
        (mcp_bp, '/api/mcp/server/<server_name>/start', 'api_mcp_server_start', ['POST']),
        (mcp_bp, '/api/mcp/server/<server_name>/stop', 'api_mcp_server_stop', ['POST']),
        (mcp_bp, '/api/mcp/tools', 'api_mcp_tools', ['GET']),
        (mcp_bp, '/api/mcp/diagnostics', 'api_mcp_diagnostics', ['GET']),
        (mcp_bp, '/api/mcp/test/<server_name>/<tool_name>', 'api_mcp_test', ['POST']),
        (mcp_bp, '/api/mcp/install', 'api_mcp_install', ['POST']),
        (mcp_bp, '/api/mcp/server/<server_name>/tools', 'api_mcp_server_tools', ['GET']),
        (mcp_bp, '/api/mcp/conversations/<session_id>/messages', 'api_mcp_conversations_messages', ['GET']),
    ],
    'memory': [
        (memory_bp, '/api/memory', 'api_memory_get', ['GET']),
        (memory_bp, '/api/memory/search', 'api_memory_search', ['GET']),
        (memory_bp, '/api/memory/stats', 'api_memory_stats', ['GET']),
        (memory_bp, '/api/memory/<conversation_id>', 'api_memory_delete', ['DELETE']),
        (memory_bp, '/api/memory/cleanup', 'api_memory_cleanup', ['POST']),
    ],
    'documents': [
        (document_bp, '/api/documents/upload', 'api_documents_upload', ['POST']),
        (document_bp, '/api/documents', 'api_documents_list', ['GET']),
        (document_bp, '/api/documents/<doc_id>', 'api_documents_get', ['GET']),
        (document_bp, '/api/documents/search', 'api_documents_search', ['GET']),
        (document_bp, '/api/documents/<doc_id>', 'api_documents_delete', ['DELETE']),
        (document_bp, '/api/documents/stats', 'api_documents_stats', ['GET']),
        (document_bp, '/api/rag/index', 'api_rag_index', ['POST']),
        (document_bp, '/api/rag/search', 'api_rag_search', ['GET']),
        (document_bp, '/api/rag/stats', 'api_rag_stats', ['GET']),
    ],
    'conversations': [
        (conversation_bp, '/api/conversations', 'api_conversations_list', ['GET']),
        (conversation_bp, '/api/conversations/<session_id>', 'api_conversations_get', ['GET']),
        (conversation_bp, '/api/conversations/<session_id>', 'api_conversations_delete', ['DELETE']),
        (conversation_bp, '/api/snapshots', 'api_snapshots_list', ['GET']),
        (conversation_bp, '/api/snapshots/restore', 'api_snapshots_restore', ['POST']),
        (conversation_bp, '/api/snapshots/<snapshot_id>', 'api_snapshots_delete', ['DELETE']),
        (conversation_bp, '/api/snapshots/<snapshot_id>/download', 'api_snapshots_download', ['GET']),
        (conversation_bp, '/api/conversation/process', 'api_conversation_process', ['POST']),
    ],
    'settings': [
        (settings_bp, '/api/config', 'api_config_get', ['GET']),
        (settings_bp, '/api/config', 'api_config_post', ['POST']),
        (settings_bp, '/api/system_prompt', 'api_system_prompt_get', ['GET']),
        (settings_bp, '/api/system_prompt', 'api_system_prompt_post', ['POST']),
        (settings_bp, '/api/config/read', 'api_config_read', ['GET']),
        (settings_bp, '/api/config/save', 'api_config_save', ['POST']),
        (settings_bp, '/api/fallback_config', 'api_fallback_config_get', ['GET']),
        (settings_bp, '/api/fallback_config', 'api_fallback_config_post', ['POST']),
        (settings_bp, '/api/settings', 'api_settings_get', ['GET']),
        (settings_bp, '/api/settings', 'api_settings_post', ['POST']),
    ],
    'voice': [
        (voice_bp, '/api/voice/stats', 'api_voice_stats', ['GET']),
        (voice_bp, '/api/voice/transcribe', 'api_voice_transcribe', ['POST']),
        (voice_bp, '/api/voice/tts', 'api_voice_tts', ['POST']),
        (voice_bp, '/api/voice/tts/providers', 'api_voice_tts_providers', ['GET']),
    ],
    'messaging': [
        (messaging_bp, '/api/messaging/stats', 'api_messaging_stats', ['GET']),
        (messaging_bp, '/api/telegram/message', 'api_telegram_message', ['POST']),
        (messaging_bp, '/api/messaging/chats', 'api_messaging_chats', ['GET']),
        (messaging_bp, '/api/messaging/chat/<channel>/<user_id>', 'api_messaging_chat_get', ['GET']),
        (messaging_bp, '/api/messaging/chat/<channel>/<user_id>', 'api_messaging_chat_delete', ['DELETE']),
        (messaging_bp, '/api/whatsapp/webhook', 'api_whatsapp_webhook', ['POST']),
    ],
    'oauth': [
        (oauth_bp, '/api/oauth/codex/start', 'api_oauth_codex_start', ['GET']),
        (oauth_bp, '/api/oauth/codex/exchange', 'api_oauth_codex_exchange', ['POST']),
        (oauth_bp, '/api/oauth/codex/status', 'api_oauth_codex_status', ['GET']),
        (oauth_bp, '/api/oauth/codex/revoke', 'api_oauth_codex_revoke', ['POST']),
        (oauth_bp, '/api/oauth/copilot/start', 'api_oauth_copilot_start', ['GET']),
        (oauth_bp, '/api/oauth/copilot/poll', 'api_oauth_copilot_poll', ['GET']),
        (oauth_bp, '/api/oauth/copilot/status', 'api_oauth_copilot_status', ['GET']),
        (oauth_bp, '/api/oauth/copilot/revoke', 'api_oauth_copilot_revoke', ['POST']),
        (oauth_bp, '/api/session/claude_web/store', 'api_session_claude_web_store', ['POST']),
        (oauth_bp, '/api/session/claude_web/status', 'api_session_claude_web_status', ['GET']),
        (oauth_bp, '/api/session/claude_web/clear', 'api_session_claude_web_clear', ['POST']),
        (oauth_bp, '/api/session/chatgpt_web/store', 'api_session_chatgpt_web_store', ['POST']),
        (oauth_bp, '/api/session/chatgpt_web/status', 'api_session_chatgpt_web_status', ['GET']),
        (oauth_bp, '/api/session/chatgpt_web/clear', 'api_session_chatgpt_web_clear', ['POST']),
    ],
    'nvidia': [
        (nvidia_bp, '/api/nvidia/test_model', 'api_nvidia_test_model', ['POST']),
        (nvidia_bp, '/api/nvidia/test_models', 'api_nvidia_test_models', ['POST']),
    ],
    'catalog': [
        (catalog_bp, '/api/catalog/stats', 'api_catalog_stats', ['GET']),
        (catalog_bp, '/api/catalog/models', 'api_catalog_models', ['GET']),
        (catalog_bp, '/api/get_models', 'api_get_models', ['GET']),
        (catalog_bp, '/api/models/cache/status', 'api_models_cache_status', ['GET']),
        (catalog_bp, '/api/models/cache/clear', 'api_models_cache_clear', ['POST']),
        (catalog_bp, '/api/models/cache/refresh', 'api_models_cache_refresh', ['POST']),
    ],
    'analytics': [
        (analytics_bp, '/api/cache/semantic/stats', 'api_cache_semantic_stats', ['GET']),
        (analytics_bp, '/api/cache/semantic/clear', 'api_cache_semantic_clear', ['POST']),
        (analytics_bp, '/api/tools/optimizer/stats', 'api_tools_optimizer_stats', ['GET']),
        (analytics_bp, '/api/quality/stats', 'api_quality_stats', ['GET']),
        (analytics_bp, '/api/image/stats', 'api_image_stats', ['GET']),
        (analytics_bp, '/api/image/analyze', 'api_image_analyze', ['POST']),
    ],
    'ui': [
        (ui_bp, '/', 'index', ['GET']),
        (ui_bp, '/ui_bootstrap.js', 'ui_bootstrap', ['GET']),
        (ui_bp, '/ui_main.js', 'ui_main', ['GET']),
        (ui_bp, '/api/ui_ping', 'api_ui_ping', ['GET']),
        (ui_bp, '/api/status', 'api_status', ['GET']),
    ],
    'bubble': [
        (bubble_bp, '/api/bubble/status', 'api_bubble_status', ['GET']),
        (bubble_bp, '/api/bubble/register', 'api_bubble_register', ['POST']),
        (bubble_bp, '/api/set_model', 'api_set_model', ['POST']),
        (bubble_bp, '/api/bubble/device-id', 'api_bubble_device_id', ['POST']),
        (bubble_bp, '/api/bubble/config', 'api_bubble_config', ['GET']),
        (bubble_bp, '/api/bubble/devices', 'api_bubble_devices_list', ['GET']),
        (bubble_bp, '/api/bubble/devices', 'api_bubble_devices_create', ['POST']),
        (bubble_bp, '/api/bubble/devices/<device_id>', 'api_bubble_devices_patch', ['PATCH']),
        (bubble_bp, '/api/bubble/devices/<device_id>', 'api_bubble_devices_delete', ['DELETE']),
    ],
    'legacy': [
        (legacy_bp, '/health', 'health', ['GET']),
        (legacy_bp, '/entities', 'entities', ['GET']),
        (legacy_bp, '/entity/<entity_id>/state', 'entity_state', ['GET']),
        (legacy_bp, '/message', 'message', ['POST']),
        (legacy_bp, '/service/call', 'service_call', ['POST']),
        (legacy_bp, '/execute/automation', 'execute_automation', ['POST']),
        (legacy_bp, '/execute/script', 'execute_script', ['POST']),
        (legacy_bp, '/conversation/clear', 'conversation_clear', ['POST']),
        (legacy_bp, '/api/alexa/webhook', 'api_alexa_webhook', ['POST']),
    ],
    'system': [
        (system_bp, '/api/system/features', 'api_system_features', ['GET']),
        (system_bp, '/api/ha_logs', 'api_ha_logs', ['GET']),
        (system_bp, '/api/browser-errors', 'api_browser_errors_post', ['POST']),
        (system_bp, '/api/browser-errors', 'api_browser_errors_get', ['GET']),
        (system_bp, '/api/addon/restart', 'api_addon_restart', ['POST']),
    ],
    'usage': [
        (usage_bp, '/api/usage_stats', 'api_usage_stats', ['GET']),
        (usage_bp, '/api/usage_stats/today', 'api_usage_stats_today', ['GET']),
        (usage_bp, '/api/usage_stats/reset', 'api_usage_stats_reset', ['POST']),
    ],
    'dashboard': [
        (dashboard_bp, '/dashboard_api/states', 'dashboard_api_states', ['GET']),
        (dashboard_bp, '/dashboard_api/history', 'dashboard_api_history', ['GET']),
        (dashboard_bp, '/dashboard_api/services/<domain>/<service>', 'dashboard_api_services', ['POST']),
        (dashboard_bp, '/custom_dashboards/<name>', 'custom_dashboards', ['GET']),
        (dashboard_bp, '/api/dashboard_html/<name>', 'api_dashboard_html', ['GET']),
        (dashboard_bp, '/custom_dashboards', 'custom_dashboards_list', ['GET']),
    ],
    'files': [
        (file_bp, '/api/files/list', 'api_files_list', ['GET']),
        (file_bp, '/api/files/read', 'api_files_read', ['GET']),
    ],
    'scheduled': [
        (scheduled_bp, '/api/scheduled/stats', 'api_scheduled_stats', ['GET']),
        (scheduled_bp, '/api/scheduled/tasks', 'api_scheduled_tasks_list', ['GET']),
        (scheduled_bp, '/api/scheduled/tasks', 'api_scheduled_tasks_create', ['POST']),
        (scheduled_bp, '/api/scheduled/tasks/<task_id>', 'api_scheduled_tasks_delete', ['DELETE']),
        (scheduled_bp, '/api/scheduled/tasks/<task_id>/toggle', 'api_scheduled_tasks_toggle', ['POST']),
        (scheduled_bp, '/api/agent/scheduler', 'api_agent_scheduler', ['POST']),
        (scheduled_bp, '/api/agent/scheduler/sessions', 'api_agent_scheduler_sessions', ['GET']),
        (scheduled_bp, '/api/agent/scheduler/session/<session_id>', 'api_agent_scheduler_session_delete', ['DELETE']),
    ],
}


def register_blueprints(app: Flask) -> None:
    """Register all Flask blueprints with the app.

    This function is called during app initialization to set up route blueprints.
    Registers all blueprints (chat, agents, mcp, memory, etc.) and their routes.

    The actual route implementations are defined in api.py and registered
    dynamically via add_url_rule on each blueprint.
    """
    # Register all blueprints with the app
    app.register_blueprint(chat_bp)
    app.register_blueprint(agents_bp)
    app.register_blueprint(mcp_bp)
    app.register_blueprint(memory_bp)
    app.register_blueprint(document_bp)
    app.register_blueprint(conversation_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(voice_bp)
    app.register_blueprint(messaging_bp)
    app.register_blueprint(oauth_bp)
    app.register_blueprint(nvidia_bp)
    app.register_blueprint(catalog_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(ui_bp)
    app.register_blueprint(bubble_bp)
    app.register_blueprint(legacy_bp)
    app.register_blueprint(system_bp)
    app.register_blueprint(usage_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(file_bp)
    app.register_blueprint(scheduled_bp)
