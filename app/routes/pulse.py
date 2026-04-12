from flask import Blueprint, request, jsonify, session
from app.models import User
from app.services.pulse_service import search_creator_service
from app.services.billing import billing_enabled, get_user_entitlements
from app.services.oauth_token_store import get_valid_access_token, require_user_session_user_id
import requests
from datetime import date, datetime, timedelta

bp = Blueprint("pulse", __name__)

@bp.route("/api/pulse/search", methods=["POST"])
def pulse_search():
    try:
        if billing_enabled():
            user_id = session.get("user_id")
            user = User.query.get(user_id) if user_id else None
            entitlements = get_user_entitlements(user)
            if not entitlements["pulse_allowed"]:
                return jsonify({"success": False, "error": "Pulse ist in deinem aktuellen Abo nicht freigeschaltet."}), 403
        data = request.get_json(force=True)
        username = data.get("username", "").strip()
        platform = data.get("platform", "").strip().lower()
        realname = data.get("realname", "").strip() if data.get("realname") else None
        deepsearch = bool(data.get("deepsearch", False))
        if not username or not platform:
            return jsonify({"success": False, "error": "username und platform sind Pflichtfelder."}), 400
        result = search_creator_service(username, platform, realname, deepsearch)
        return jsonify({
            "success": True,
            "query": {
                "username": username,
                "platform": platform,
                "realname": realname or "",
                "deepsearch": deepsearch
            },
            **result
        })
    except ValueError as ve:
        return jsonify({"success": False, "error": str(ve)}), 400
    except Exception as ex:
        return jsonify({"success": False, "error": "Internal error: " + str(ex)}), 500


@bp.route("/api/pulse/me/<platform>", methods=["GET"])
def pulse_me(platform: str):
    """
    Fetches data for the currently connected account (OAuth) for supported platforms.
    """
    try:
        user_id = require_user_session_user_id(session)
        platform = (platform or "").strip().lower()

        if platform == "twitch":
            token = get_valid_access_token(user_id, "twitch")
            if not token:
                return jsonify({"success": False, "error": "Twitch ist nicht verbunden."}), 400
            # Access app config via current_app to avoid circular imports in blueprint module scope
            from flask import current_app

            client_id = current_app.config.get("TWITCH_CLIENT_ID")
            if not client_id:
                return jsonify({"success": False, "error": "TWITCH_CLIENT_ID fehlt."}), 400

            headers = {"Client-Id": client_id, "Authorization": f"Bearer {token}"}
            me = requests.get("https://api.twitch.tv/helix/users", headers=headers, timeout=10)
            me.raise_for_status()
            items = (me.json() or {}).get("data") or []
            if not items:
                return jsonify({"success": False, "error": "Twitch User konnte nicht geladen werden."}), 400
            user = items[0]
            user_id_twitch = user.get("id")
            profile_url = f"https://www.twitch.tv/{user.get('login') or ''}".rstrip("/")

            followers = None
            if user_id_twitch:
                try:
                    f_res = requests.get(
                        "https://api.twitch.tv/helix/channels/followers",
                        headers=headers,
                        params={"broadcaster_id": user_id_twitch, "first": 1},
                        timeout=10,
                    )
                    if f_res.ok:
                        followers = (f_res.json() or {}).get("total")
                except requests.RequestException:
                    followers = None

            stream_info = None
            if user_id_twitch:
                try:
                    s_res = requests.get(
                        "https://api.twitch.tv/helix/streams",
                        headers=headers,
                        params={"user_id": user_id_twitch, "first": 1},
                        timeout=10,
                    )
                    if s_res.ok:
                        s_items = (s_res.json() or {}).get("data") or []
                        if s_items:
                            stream_info = s_items[0]
                except requests.RequestException:
                    stream_info = None

            return jsonify(
                {
                    "success": True,
                    "creator": {
                        "display_name": user.get("display_name") or user.get("login"),
                        "username": user.get("login"),
                        "platform": "twitch",
                        "country": None,
                        "profile_url": profile_url or None,
                        "avatar": user.get("profile_image_url"),
                    },
                    "metrics": {
                        "followers": followers,
                        "views_total": user.get("view_count"),
                        "is_live": bool(stream_info),
                        "live_viewers": stream_info.get("viewer_count") if stream_info else None,
                        "live_game": stream_info.get("game_name") if stream_info else None,
                        "estimated_earnings_today_usd": None,
                        "estimated_earnings_total_usd": None,
                        "diamonds_today": None,
                        "ranking_country": None,
                    },
                    "history": [],
                    "source": {"provider": "twitch", "type": "oauth_user", "confidence": "high"},
                }
            )

        if platform == "youtube":
            token = get_valid_access_token(user_id, "google")
            if not token:
                return jsonify({"success": False, "error": "YouTube/Google ist nicht verbunden."}), 400

            headers = {"Authorization": f"Bearer {token}"}
            ch = requests.get(
                "https://www.googleapis.com/youtube/v3/channels",
                headers=headers,
                params={"part": "snippet,statistics", "mine": "true", "maxResults": 1},
                timeout=10,
            )
            if ch.status_code >= 400:
                return jsonify({"success": False, "error": "YouTube Channel konnte nicht geladen werden."}), 400
            items = (ch.json() or {}).get("items") or []
            if not items:
                return jsonify({"success": False, "error": "Kein YouTube Channel gefunden."}), 400

            channel = items[0]
            snippet = channel.get("snippet") or {}
            stats = channel.get("statistics") or {}
            thumb = ((snippet.get("thumbnails") or {}).get("high") or {}).get("url")
            title = snippet.get("title")
            custom = snippet.get("customUrl") or ""
            profile_url = f"https://www.youtube.com/{custom}" if custom.startswith("@") else (f"https://www.youtube.com/@{custom}" if custom else None)

            subscribers = stats.get("subscriberCount")
            views_total = stats.get("viewCount")
            videos_total = stats.get("videoCount")

            return jsonify(
                {
                    "success": True,
                    "creator": {
                        "display_name": title or custom or "YouTube",
                        "username": custom.lstrip("@") if custom else "",
                        "platform": "youtube",
                        "country": None,
                        "profile_url": profile_url,
                        "avatar": thumb,
                    },
                    "metrics": {
                        "subscribers": int(subscribers) if subscribers is not None else None,
                        "views_total": int(views_total) if views_total is not None else None,
                        "videos_total": int(videos_total) if videos_total is not None else None,
                        "estimated_earnings_today_usd": None,
                        "estimated_earnings_total_usd": None,
                        "diamonds_today": None,
                        "ranking_country": None,
                    },
                    "history": [],
                    "source": {"provider": "youtube", "type": "oauth_user", "confidence": "high"},
                }
            )

        return jsonify({"success": False, "error": f"Platform '{platform}' nicht fuer OAuth-Me unterstuetzt."}), 400
    except PermissionError as exc:
        return jsonify({"success": False, "error": str(exc)}), 401
    except requests.RequestException:
        return jsonify({"success": False, "error": "Provider API Fehler."}), 502
    except Exception as ex:
        return jsonify({"success": False, "error": "Internal error: " + str(ex)}), 500


def _parse_ymd(value: str, field: str) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except Exception as exc:
        raise ValueError(f"Ungueltiges Datum fuer '{field}' (Format YYYY-MM-DD).") from exc


def _twitch_headers(access_token: str) -> dict:
    from flask import current_app

    client_id = current_app.config.get("TWITCH_CLIENT_ID")
    if not client_id:
        raise ValueError("TWITCH_CLIENT_ID fehlt.")
    return {"Client-Id": client_id, "Authorization": f"Bearer {access_token}"}


def _twitch_get(path: str, headers: dict, params: dict) -> dict:
    resp = requests.get(
        f"https://api.twitch.tv/helix/{path.lstrip('/')}",
        headers=headers,
        params=params,
        timeout=12,
    )
    resp.raise_for_status()
    return resp.json() or {}


@bp.route("/api/pulse/twitch/analytics", methods=["GET"])
def twitch_analytics():
    """
    Twitch Analytics aus offiziellen Helix-Endpoints (OAuth erforderlich).

    Achtung: Twitch stellt keine Revenue- oder Watchtime-Analytics via Helix fuer Drittapps bereit.
    Wir liefern aggregierbare, oeffentliche Signale (Clips/VOD Views, Counts, Top Clips/VODs).

    Query:
      - range: "7" | "30" | "custom" (default 7)
      - start/end: YYYY-MM-DD (bei custom)
      - top: int (default 10, max 25)
    """
    try:
        user_id = require_user_session_user_id(session)
        token = get_valid_access_token(user_id, "twitch")
        if not token:
            return jsonify({"success": False, "error": "Twitch ist nicht verbunden."}), 400

        range_key = (request.args.get("range") or "7").strip().lower()
        top_n = request.args.get("top") or "10"
        try:
            top_n = max(1, min(25, int(top_n)))
        except ValueError:
            top_n = 10

        today = datetime.utcnow().date()
        if range_key in {"7", "last7", "week"}:
            start_dt = today - timedelta(days=7)
            end_dt = today
        elif range_key in {"30", "last30", "month"}:
            start_dt = today - timedelta(days=30)
            end_dt = today
        elif range_key == "custom":
            start_raw = (request.args.get("start") or "").strip()
            end_raw = (request.args.get("end") or "").strip()
            if not start_raw or not end_raw:
                return jsonify({"success": False, "error": "start und end sind Pflicht bei range=custom."}), 400
            start_dt = _parse_ymd(start_raw, "start")
            end_dt = _parse_ymd(end_raw, "end")
        else:
            return jsonify({"success": False, "error": "Ungueltige range. Nutze 7, 30 oder custom."}), 400

        if start_dt > end_dt:
            return jsonify({"success": False, "error": "start darf nicht nach end liegen."}), 400
        if (end_dt - start_dt).days > 365:
            return jsonify({"success": False, "error": "Custom Range zu gross (max 365 Tage)."}), 400

        headers = _twitch_headers(token)

        # Resolve broadcaster id via /users (token-bound)
        me = _twitch_get("users", headers, {})
        users = me.get("data") or []
        if not users:
            return jsonify({"success": False, "error": "Twitch User konnte nicht geladen werden."}), 400
        broadcaster = users[0]
        broadcaster_id = broadcaster.get("id")
        if not broadcaster_id:
            return jsonify({"success": False, "error": "Twitch User-ID fehlt."}), 400

        # RFC3339 timestamps for clips
        start_rfc = datetime.combine(start_dt, datetime.min.time()).isoformat() + "Z"
        end_rfc = datetime.combine(end_dt + timedelta(days=1), datetime.min.time()).isoformat() + "Z"

        # Collect clips with pagination (cap pages for performance)
        clips = []
        cursor = None
        pages = 0
        while pages < 5:
            pages += 1
            params = {
                "broadcaster_id": broadcaster_id,
                "started_at": start_rfc,
                "ended_at": end_rfc,
                "first": 100,
            }
            if cursor:
                params["after"] = cursor
            payload = _twitch_get("clips", headers, params)
            batch = payload.get("data") or []
            clips.extend(batch)
            cursor = (payload.get("pagination") or {}).get("cursor")
            if not cursor or not batch:
                break

        def day_key(value: str) -> str:
            # Twitch returns ISO timestamps like 2020-01-01T00:00:00Z
            try:
                return value[:10]
            except Exception:
                return "-"

        clip_daily = {}
        for item in clips:
            d = day_key(item.get("created_at") or "")
            clip_daily.setdefault(d, {"clip_views": 0, "clip_count": 0})
            clip_daily[d]["clip_count"] += 1
            clip_daily[d]["clip_views"] += int(item.get("view_count") or 0)

        top_clips = sorted(
            [
                {
                    "id": item.get("id"),
                    "url": item.get("url"),
                    "title": item.get("title") or "",
                    "created_at": item.get("created_at"),
                    "views": int(item.get("view_count") or 0),
                    "thumbnail_url": item.get("thumbnail_url"),
                    "duration": item.get("duration"),
                }
                for item in clips
                if item.get("url")
            ],
            key=lambda x: x["views"],
            reverse=True,
        )[:top_n]

        # Collect recent VODs (videos) and filter by created_at
        vods = []
        cursor = None
        pages = 0
        while pages < 5:
            pages += 1
            params = {"user_id": broadcaster_id, "first": 100}
            if cursor:
                params["after"] = cursor
            payload = _twitch_get("videos", headers, params)
            batch = payload.get("data") or []
            if not batch:
                break

            for item in batch:
                created = item.get("created_at") or ""
                if created and created[:10] < start_dt.strftime("%Y-%m-%d"):
                    # We reached older videos; we can stop early.
                    continue
                vods.append(item)
            cursor = (payload.get("pagination") or {}).get("cursor")
            if not cursor:
                break

        vods_in_range = []
        for item in vods:
            created = item.get("created_at") or ""
            if not created:
                continue
            d = created[:10]
            if start_dt.strftime("%Y-%m-%d") <= d <= end_dt.strftime("%Y-%m-%d"):
                vods_in_range.append(item)

        vod_daily = {}
        for item in vods_in_range:
            d = day_key(item.get("created_at") or "")
            vod_daily.setdefault(d, {"vod_views": 0, "vod_count": 0})
            vod_daily[d]["vod_count"] += 1
            vod_daily[d]["vod_views"] += int(item.get("view_count") or 0)

        top_vods = sorted(
            [
                {
                    "id": item.get("id"),
                    "url": item.get("url"),
                    "title": item.get("title") or "",
                    "created_at": item.get("created_at"),
                    "views": int(item.get("view_count") or 0),
                    "thumbnail_url": item.get("thumbnail_url"),
                    "duration": item.get("duration"),
                    "type": item.get("type"),
                }
                for item in vods_in_range
                if item.get("url")
            ],
            key=lambda x: x["views"],
            reverse=True,
        )[:top_n]

        # Build full day series for chart rendering (fill missing days)
        series = []
        cur = start_dt
        while cur <= end_dt:
            key = cur.strftime("%Y-%m-%d")
            c = clip_daily.get(key, {"clip_views": 0, "clip_count": 0})
            v = vod_daily.get(key, {"vod_views": 0, "vod_count": 0})
            series.append(
                {
                    "day": key,
                    **c,
                    **v,
                }
            )
            cur += timedelta(days=1)

        totals = {
            "clip_views": sum(item["clip_views"] for item in series),
            "clip_count": sum(item["clip_count"] for item in series),
            "vod_views": sum(item["vod_views"] for item in series),
            "vod_count": sum(item["vod_count"] for item in series),
        }

        return jsonify(
            {
                "success": True,
                "range": {
                    "start": start_dt.strftime("%Y-%m-%d"),
                    "end": end_dt.strftime("%Y-%m-%d"),
                    "mode": range_key,
                    "top": top_n,
                },
                "creator": {
                    "display_name": broadcaster.get("display_name") or broadcaster.get("login"),
                    "username": broadcaster.get("login"),
                    "profile_url": f"https://www.twitch.tv/{broadcaster.get('login')}" if broadcaster.get("login") else None,
                    "avatar": broadcaster.get("profile_image_url"),
                },
                "totals": totals,
                "timeseries": series,
                "top_clips": top_clips,
                "top_vods": top_vods,
                "source": {
                    "provider": "twitch_helix",
                    "type": "oauth_user",
                    "confidence": "high",
                    "note": "Keine Revenue/Watchtime-Analytics via Helix verfuegbar; nur Clips/VOD Views/Counts.",
                },
            }
        )
    except PermissionError as exc:
        return jsonify({"success": False, "error": str(exc)}), 401
    except ValueError as exc:
        return jsonify({"success": False, "error": str(exc)}), 400
    except requests.RequestException:
        return jsonify({"success": False, "error": "Twitch API Fehler (Token/Netzwerk)."}), 502
    except Exception as ex:
        return jsonify({"success": False, "error": "Internal error: " + str(ex)}), 500


@bp.route("/api/pulse/youtube/analytics", methods=["GET"])
def youtube_analytics():
    """
    Returns YouTube Analytics for the connected Google account.

    Query:
      - range: "7" | "30" | "custom" (default 7)
      - start: YYYY-MM-DD (required if range=custom)
      - end: YYYY-MM-DD (required if range=custom)
      - top: int (default 10, max 25)
    """
    try:
        user_id = require_user_session_user_id(session)
        token = get_valid_access_token(user_id, "google")
        if not token:
            return jsonify({"success": False, "error": "YouTube/Google ist nicht verbunden."}), 400

        range_key = (request.args.get("range") or "7").strip().lower()
        top_n = request.args.get("top") or "10"
        try:
            top_n = max(1, min(25, int(top_n)))
        except ValueError:
            top_n = 10

        today = datetime.utcnow().date()
        if range_key in {"7", "last7", "week"}:
            start_dt = today - timedelta(days=7)
            end_dt = today
        elif range_key in {"30", "last30", "month"}:
            start_dt = today - timedelta(days=30)
            end_dt = today
        elif range_key == "custom":
            start_raw = (request.args.get("start") or "").strip()
            end_raw = (request.args.get("end") or "").strip()
            if not start_raw or not end_raw:
                return jsonify({"success": False, "error": "start und end sind Pflicht bei range=custom."}), 400
            start_dt = _parse_ymd(start_raw, "start")
            end_dt = _parse_ymd(end_raw, "end")
        else:
            return jsonify({"success": False, "error": "Ungueltige range. Nutze 7, 30 oder custom."}), 400

        # Basic sanity limits for custom ranges
        if start_dt > end_dt:
            return jsonify({"success": False, "error": "start darf nicht nach end liegen."}), 400
        if (end_dt - start_dt).days > 365:
            return jsonify({"success": False, "error": "Custom Range zu gross (max 365 Tage)."}), 400

        headers = {"Authorization": f"Bearer {token}"}

        def analytics_get(params: dict):
            resp = requests.get(
                "https://youtubeanalytics.googleapis.com/v2/reports",
                headers=headers,
                params=params,
                timeout=12,
            )
            resp.raise_for_status()
            return resp.json() or {}

        start_str = start_dt.strftime("%Y-%m-%d")
        end_str = end_dt.strftime("%Y-%m-%d")

        # Timeseries (daily): views, watchtime (minutes), subs gained/lost
        series = analytics_get(
            {
                "ids": "channel==MINE",
                "startDate": start_str,
                "endDate": end_str,
                "metrics": "views,estimatedMinutesWatched,subscribersGained,subscribersLost",
                "dimensions": "day",
                "sort": "day",
            }
        )

        rows = series.get("rows") or []
        timeseries = [
            {
                "day": row[0],
                "views": int(row[1] or 0),
                "watch_minutes": int(row[2] or 0),
                "subs_gained": int(row[3] or 0),
                "subs_lost": int(row[4] or 0),
                "subs_net": int(row[3] or 0) - int(row[4] or 0),
            }
            for row in rows
        ]

        totals = {
            "views": sum(item["views"] for item in timeseries),
            "watch_minutes": sum(item["watch_minutes"] for item in timeseries),
            "subs_gained": sum(item["subs_gained"] for item in timeseries),
            "subs_lost": sum(item["subs_lost"] for item in timeseries),
        }
        totals["subs_net"] = totals["subs_gained"] - totals["subs_lost"]

        # Top videos by views in range
        top_videos_report = analytics_get(
            {
                "ids": "channel==MINE",
                "startDate": start_str,
                "endDate": end_str,
                "metrics": "views,estimatedMinutesWatched",
                "dimensions": "video",
                "sort": "-views",
                "maxResults": str(top_n),
            }
        )
        top_rows = top_videos_report.get("rows") or []
        video_ids = [row[0] for row in top_rows if row and row[0]]
        video_metrics = {
            row[0]: {
                "views": int(row[1] or 0),
                "watch_minutes": int(row[2] or 0),
            }
            for row in top_rows
            if row and row[0]
        }

        # Enrich with video titles/thumbnails via YouTube Data API (OAuth works, too).
        video_details = {}
        if video_ids:
            v_resp = requests.get(
                "https://www.googleapis.com/youtube/v3/videos",
                headers=headers,
                params={
                    "part": "snippet,statistics",
                    "id": ",".join(video_ids[:50]),
                    "maxResults": len(video_ids[:50]),
                },
                timeout=12,
            )
            if v_resp.ok:
                for item in (v_resp.json() or {}).get("items") or []:
                    vid = item.get("id")
                    snippet = item.get("snippet") or {}
                    stats = item.get("statistics") or {}
                    thumbs = snippet.get("thumbnails") or {}
                    thumb = (thumbs.get("high") or thumbs.get("medium") or thumbs.get("default") or {}).get("url")
                    video_details[vid] = {
                        "title": snippet.get("title") or "",
                        "published_at": snippet.get("publishedAt"),
                        "thumbnail": thumb,
                        "like_count": int(stats.get("likeCount")) if stats.get("likeCount") is not None else None,
                        "comment_count": int(stats.get("commentCount")) if stats.get("commentCount") is not None else None,
                    }

        top_videos = []
        for vid in video_ids:
            meta = video_details.get(vid, {})
            metric = video_metrics.get(vid, {"views": 0, "watch_minutes": 0})
            top_videos.append(
                {
                    "video_id": vid,
                    "url": f"https://www.youtube.com/watch?v={vid}",
                    "title": meta.get("title") or vid,
                    "thumbnail": meta.get("thumbnail"),
                    "published_at": meta.get("published_at"),
                    "views": metric["views"],
                    "watch_minutes": metric["watch_minutes"],
                    "like_count": meta.get("like_count"),
                    "comment_count": meta.get("comment_count"),
                }
            )

        return jsonify(
            {
                "success": True,
                "range": {"start": start_str, "end": end_str, "mode": range_key, "top": top_n},
                "totals": totals,
                "timeseries": timeseries,
                "top_videos": top_videos,
                "source": {"provider": "youtube_analytics", "type": "oauth_user", "confidence": "high"},
            }
        )
    except PermissionError as exc:
        return jsonify({"success": False, "error": str(exc)}), 401
    except ValueError as exc:
        return jsonify({"success": False, "error": str(exc)}), 400
    except requests.RequestException:
        return jsonify({"success": False, "error": "YouTube API Fehler (Token/Quota/Netzwerk)."}), 502
    except Exception as ex:
        return jsonify({"success": False, "error": "Internal error: " + str(ex)}), 500
