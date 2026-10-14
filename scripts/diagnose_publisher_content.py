#!/usr/bin/env python3
"""One-shot publisher identity/content metadata check; never emits response bodies."""
import datetime
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

BASE = "https://discord.com/api/v10"
CHANNEL_ID = "1456350065223270435"
MESSAGE_ID = "1559722825512779959"
MAX_BODY = 512 * 1024
TIMEOUT = 15


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def normalize_token(raw):
    value = raw.strip()
    if value.startswith("Bot "):
        value = value[4:]
    return value.strip()


def identifier(value):
    return value if isinstance(value, str) and re.fullmatch(r"[1-9][0-9]{16,19}", value) else None


def fetch(token, path, opener=None):
    if path not in ("/users/@me", "/oauth2/applications/@me", f"/channels/{CHANNEL_ID}/messages/{MESSAGE_ID}"):
        return {"error": "unsupported_path"}, None
    request = urllib.request.Request(BASE + path, headers={
        "Authorization": "Bot " + token,
        "Accept": "application/json",
        "User-Agent": "DiscrawlPublisherMetadataDiagnostic/1",
    })
    opener = opener or urllib.request.build_opener(NoRedirect())
    started = time.monotonic()
    meta = {}
    try:
        with opener.open(request, timeout=TIMEOUT) as response:
            meta["http_status"] = response.status
            if response.status != 200:
                meta["error"] = "unexpected_http_status"
                return meta, None
            raw = response.read(MAX_BODY + 1)
            meta["response_bytes"] = len(raw)
            if len(raw) > MAX_BODY:
                meta["error"] = "response_size_limit"
                return meta, None
            try:
                payload = json.loads(raw)
            except (ValueError, UnicodeError):
                meta["error"] = "invalid_json"
                return meta, None
            if not isinstance(payload, dict):
                meta["error"] = "unexpected_json_shape"
                return meta, None
            return meta, payload
    except urllib.error.HTTPError as exc:
        meta.update(http_status=exc.code, error="http_error")
        exc.close()  # Do not inspect or emit error response bodies.
        return meta, None
    except (OSError, ValueError):
        meta["error"] = "transport_error"
        return meta, None
    finally:
        meta["elapsed_ms"] = round((time.monotonic() - started) * 1000)


def diagnose(raw_token, fetcher=fetch):
    report = {"schema": "discrawl.publisher-content-diagnostic.v1", "complete": False,
              "checked_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "requests": []}
    token = normalize_token(raw_token)
    if not token:
        report["error"] = "missing_workflow_token"
        return report
    identity = None
    for label, path in [("identity", "/users/@me"), ("application", "/oauth2/applications/@me"),
                        ("message", f"/channels/{CHANNEL_ID}/messages/{MESSAGE_ID}")]:
        meta, payload = fetcher(token, path)
        report["requests"].append({"operation": label, **meta})
        if payload is None:
            report["error"] = label + "_request_failed"
            return report
        if label == "identity":
            identity = identifier(payload.get("id"))
            if not identity or payload.get("bot") is not True:
                report["error"] = "expected_bot_identity"
                return report
            report["bot_id"] = identity
        elif label == "application":
            app_id = identifier(payload.get("id"))
            flags = payload.get("flags")
            if not app_id or type(flags) is not int or not 0 <= flags < 2**64:
                report["error"] = "unsupported_application_metadata"
                return report
            bot = payload.get("bot") or {}
            app_bot_id = identifier(bot.get("id")) if isinstance(bot, dict) else None
            report["application"] = {"id": app_id, "bot_id": app_bot_id, "flags": flags,
                "message_content_flag": bool(flags & (1 << 18)),
                "message_content_limited_flag": bool(flags & (1 << 19)),
                "guild_members_flag": bool(flags & (1 << 14)),
                "guild_members_limited_flag": bool(flags & (1 << 15))}
            if app_bot_id is not None and app_bot_id != identity:
                report["error"] = "application_bot_identity_mismatch"
                return report
        else:
            if payload.get("id") != MESSAGE_ID or payload.get("channel_id") != CHANNEL_ID:
                report["error"] = "message_identity_mismatch"
                return report
            content = payload.get("content")
            if content is not None and not isinstance(content, str):
                report["error"] = "unsupported_content_shape"
                return report
            author = payload.get("author") or {}
            mentions = payload.get("mentions") or []
            if not isinstance(author, dict) or not isinstance(mentions, list):
                report["error"] = "unsupported_message_metadata"
                return report
            report["message"] = {"id": MESSAGE_ID, "channel_id": CHANNEL_ID,
                "content_field_present": "content" in payload,
                "content_chars": len(content or ""),
                "content_utf8_bytes": len((content or "").encode("utf-8")),
                "author_is_self": author.get("id") == identity,
                "author_is_bot": author.get("bot") if type(author.get("bot")) is bool else None,
                "mentions_self": any(isinstance(x, dict) and x.get("id") == identity for x in mentions)}
            for field in ("embeds", "attachments", "components"):
                value = payload.get(field) or []
                if not isinstance(value, list):
                    report["error"] = "unsupported_message_metadata"
                    return report
                report["message"][field + "_count"] = len(value)
    report["complete"] = True
    return report


def main():
    try:
        if len(sys.argv) != 1:
            result = {"complete": False, "error": "arguments_not_supported"}
        else:
            result = diagnose(os.environ.get("DISCORD_BOT_TOKEN", ""))
    except Exception:
        # Error strings, response objects and exception traces can contain secrets.
        result = {"complete": False, "error": "internal_diagnostic_error"}
    print(json.dumps(result, sort_keys=True), flush=True)
    return 0 if result.get("complete") else 1


if __name__ == "__main__":
    sys.exit(main())
