import re
from typing import Any, Dict, List, Optional


# 公共头部（前三行）
HEADER_RE = re.compile(
    r"""^🌟监控到(?P<event>[^\n]+)\n
你关注的用户:\s*(?P<username>.+?)\(备注:\s*(?P<remark>.+?)\)\s*(?:\([^)]+\))?\n
用户所属分组:\s*(?P<group>[^\n]+)
""",
    re.M | re.X,
)

# 1) 新推文（正文直接吃到块结束）
PAT_NEW_TWEET = re.compile(
    r"""^🌟监控到新推文\n
你关注的用户:\s*(?P<username>.*?)\(备注:\s*(?P<remark>.*?)\)\s*(?:\([^)]+\))?\n
用户所属分组:\s*(?P<group>[^\n]*)\n
推文内容:\s*(?P<tweet>[\s\S]*)$
""",
    re.X,
)

# 2) 新推文回复（用“回帖内容:”作为分隔锚点，回帖吃到块结束）
PAT_NEW_REPLY = re.compile(
    r"""^🌟监控到新推文回复\n
你关注的用户:\s*(?P<username>.+?)\(备注:\s*(?P<remark>.+?)\)\s*(?:\([^)]+\))?\n
用户所属分组:\s*(?P<group>[^\n]+)\n
上文内容:\s*(?P<parent>[\s\S]*?)\n回帖内容:\s*(?P<reply>[\s\S]*)$
""",
    re.X,
)

# 3) 新关注动态（用户列表吃到块结束）
PAT_NEW_FOLLOW = re.compile(
    r"""^🌟监控到新关注动态\n
你关注的用户:\s*(?P<username>.+?)\(备注:\s*(?P<remark>.+?)\)\s*(?:\([^)]+\))?\n
用户所属分组:\s*(?P<group>[^\n]+)\n
用户列表:\n(?P<users_block>[\s\S]*)$
""",
    re.X,
)

# 4) 删除推文回复
PAT_DELETE_TWEET_REPLY = re.compile(
    r"""^🌟监控到删除推文\n
你关注的用户:\s*(?P<username>.+?)\(备注:\s*(?P<remark>.+?)\)\s*(?:\([^)]+\))?\n
用户所属分组:\s*(?P<group>[^\n]+)\n
上文内容:\s*(?P<parent>[\s\S]*?)\n回帖内容:\s*(?P<reply>[\s\S]*)$
""",
    re.X,
)

# 4) 删除推文
PAT_DELETE_TWEET = re.compile(
    r"""^🌟监控到删除推文\n
你关注的用户:\s*(?P<username>.+?)\(备注:\s*(?P<remark>.+?)\)\s*(?:\([^)]+\))?\n
用户所属分组:\s*(?P<group>[^\n]+)\s*$
""",
    re.X,
)

# 5) 新推文引用（引用内容吃到块结束）
PAT_NEW_QUOTE = re.compile(
    r"""^🌟监控到新推文引用\n
你关注的用户:\s*(?P<username>.+?)\(备注:\s*(?P<remark>.+?)\)\s*(?:\([^)]+\))?\n
用户所属分组:\s*(?P<group>[^\n]+)\n
引用内容:\s*(?P<quote>[\s\S]*)$
""",
    re.X,
)


TYPE_PATTERNS = [
    ("新推文", PAT_NEW_TWEET),
    ("新推文回复", PAT_NEW_REPLY),
    ("新关注动态", PAT_NEW_FOLLOW),
    ("删除推文回复", PAT_DELETE_TWEET_REPLY),
    ("删除推文", PAT_DELETE_TWEET),
    ("新推文引用", PAT_NEW_QUOTE),
]


def _split_blocks(text: str) -> List[str]:
    # 正确切块：按“下一条消息开头”切，而不是按空行
    return [
        b.strip()
        for b in re.findall(r"(?ms)^🌟监控到[\s\S]*?(?=^🌟监控到|\Z)", text.strip())
        if b.strip()
    ]


def _parse_users_block(users_block: str) -> List[str]:
    # 提取 bullet 行
    return re.findall(r"^\s*•\s*([^\n]+)\s*$", users_block, flags=re.M)


def parse_monitor_messages_regex(text: str) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []

    for block in _split_blocks(text):
        parsed: Optional[Dict[str, Any]] = None

        for event_name, pat in TYPE_PATTERNS:
            m = pat.match(block)
            if not m:
                continue

            gd = m.groupdict()
            item: Dict[str, Any] = {
                "event": event_name,
                "username": gd["username"].strip(),
                "remark": gd["remark"].strip(),
                "group": gd["group"].strip(),
                "data": {}
            }

            if event_name == "新推文":
                item["data"]["tweet"] = gd["tweet"].strip()

            elif event_name == "新推文回复":
                item["data"]["parent"] = gd["parent"].strip()
                item["data"]["reply"] = gd["reply"].strip()

            elif event_name == "新关注动态":
                item["data"]["followed_users"] = _parse_users_block(gd["users_block"])

            elif event_name == "删除推文回复":
                item["data"]["parent"] = gd["parent"].strip()
                item["data"]["reply"] = gd["reply"].strip()   

            elif event_name == "删除推文":
                pass

            elif event_name == "新推文引用":
                item["data"]["quote"] = gd["quote"].strip()

            parsed = item
            break

        if parsed is None:
            hm = HEADER_RE.search(block)
            if hm:
                gd = hm.groupdict()
                parsed = {
                    "event": gd["event"].strip(),
                    "username": gd["username"].strip(),
                    "remark": gd["remark"].strip(),
                    "group": gd["group"].strip(),
                    "data": {"raw": block}
                }
            else:
                parsed = {
                    "event": "",
                    "username": "",
                    "remark": "",
                    "group": "",
                    "data": {"raw": block}
                }

        results.append(parsed)

    return results

def build_pushplus_payload(text: str) -> tuple[str, str]:
    if True:
        parsed = parse_monitor_messages_regex(text)

        title = f"{parsed[0]['username']} [{parsed[0]['event']}]"

        if parsed[0]["event"] == "新推文":
            parts = [
                f"推文内容: {parsed[0]['data']['tweet']}",
            ]
        elif parsed[0]["event"] == "新推文回复":
            parts = [
                f"上文内容: {parsed[0]['data']['parent']}",
                f"回帖内容: {parsed[0]['data']['reply']}",
            ]
        elif parsed[0]["event"] == "新关注动态":
            parts = [
                f"关注用户: {', '.join(parsed[0]['data']['followed_users'])}",
            ]
        elif parsed[0]["event"] == "删除推文回复":
            parts = [
                f"上文内容: {parsed[0]['data']['parent']}",
                f"回帖内容: {parsed[0]['data']['reply']}",
            ]
        elif parsed[0]["event"] == "删除推文":
            parts = [
                f"",
            ]
        elif parsed[0]["event"] == "新推文引用":
            parts = [
                f"引用内容: {parsed[0]['data']['quote']}",
            ]
        else:
            parts = [
                f"",
            ]
    else:
        parts = [
            f"{text}",
        ]

    content = "\n\n".join(parts)
    return title, content


text="""
🌟监控到新推文引用
你关注的用户: Cooker.hl(备注:Cooker.hl)
用户所属分组: 过年红包
引用内容: Imagine if it was all a psyop, there was no investigation, 

Zach just wanted to get people to shit their pants 

and come fwd 🤣 https://x.com/zachxbt/status/2026544197269115136
"""

print(parse_monitor_messages_regex(text))
print(build_pushplus_payload(text))