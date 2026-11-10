"""Turn a Claude Code transcript export (transcript.jsonl) into a readable Markdown record.
Keeps the user's messages, Claude's replies and a short form of each tool call and result.
Drops system prompts, API request records, hidden reasoning and app bookkeeping, and redacts
email addresses, access tokens and account ids."""
import json, re, sys
src, out = sys.argv[1], sys.argv[2]
RED = [(re.compile(r'[A-Za-z0-9._%+-]+@(?!anthropic\.com)[A-Za-z0-9.-]+\.[A-Za-z]{2,}'), '[email redacted]'),
       (re.compile(r'\bgh[opsu]_[A-Za-z0-9*]{6,}'), '[token redacted]'),
       (re.compile(r'\bu_[A-Za-z0-9]{22}\b'), '[user id redacted]'),
       (re.compile(r'/(?:private/tmp|tmp)/claude-\d+/[^\s`"\')]*'), '[temp path]'),
       (re.compile(r'/Users/[^/\s`"\']+'), '~'),
       (re.compile(r'-Users-[A-Za-z0-9._]+-'), '-Users-[user]-'),
       (re.compile(r'(?<=[-rwxs@+.]\s)\s*\d+\s+[a-z][a-z0-9_]*\s+(?=staff|wheel)'), lambda m: re.sub(r'[a-z][a-z0-9_]*\s+$', '[user]  ', m.group(0)))]
def red(s):
    for p, r in RED: s = p.sub(r, s)
    return s
def strip_reminders(s):
    return re.sub(r'<system-reminder>.*?</system-reminder>', '', s, flags=re.S).strip()
def short(s, lines=25, chars=2500):
    s = s.rstrip(); L = s.split('\n'); cut = len(L) > lines or len(s) > chars
    s = '\n'.join(L[:lines])[:chars]
    return s + ('\n… (truncated)' if cut else '')
def fence(s, lang=''):
    f = '````' if '```' in s else '```'
    return f"{f}{lang}\n{s}\n{f}"
def tool_summary(name, inp):
    name = re.sub(r'^mcp__[0-9a-f-]{36}__', '', name)
    if name == 'Bash':
        return f"**Bash** — {inp.get('description','')}\n\n" + fence(short(inp.get('command',''), 40, 4000), 'bash')
    if name in ('Write',):
        return f"**Write** `{inp.get('file_path','')}`\n\n" + fence(short(inp.get('content',''), 30, 3000))
    if name == 'Edit':
        return f"**Edit** `{inp.get('file_path','')}`\n\n" + fence('- ' + short(inp.get('old_string',''), 8, 800).replace('\n', '\n- ') + '\n+ ' + short(inp.get('new_string',''), 12, 1200).replace('\n', '\n+ '), 'diff')
    if name == 'Read':
        return f"**Read** `{inp.get('file_path','')}`"
    keep = {k: v for k, v in inp.items() if k not in ('_consent',)}
    return f"**{name}**\n\n" + fence(short(json.dumps(keep, ensure_ascii=False, indent=1), 25, 2000), 'json')
def result_text(c):
    if isinstance(c, str): return c
    parts = []
    for b in c or []:
        if b.get('type') == 'text': parts.append(b['text'])
        elif b.get('type') == 'image': parts.append('[image]')
    return '\n'.join(parts)
recs = [json.loads(l) for l in open(src)]
msgs = [r for r in recs if r.get('type') in ('user', 'assistant') and not r.get('isSidechain') and r.get('message')]
outl = ["# Session transcript: HMS re-OCR quality review", "",
        "A readable record of the Claude Code session in which this repository's analysis was planned and carried out. "
        "It keeps the user's messages, Claude's replies, and a shortened form of each tool call and its result. "
        "System prompts, hidden reasoning and app bookkeeping are left out; long outputs are truncated; email addresses, access tokens and account ids are redacted. "
        "Generated with `docs/transcript_to_md.py` from the session export.", ""]
for r in msgs:
    m = r['message']; role = m.get('role'); content = m.get('content')
    ts = (r.get('timestamp') or '')[:16].replace('T', ' ')
    if isinstance(content, str): content = [{'type': 'text', 'text': content}]
    for b in content:
        t = b.get('type')
        if role == 'user' and t == 'text':
            txt = strip_reminders(b['text'])
            if not txt or txt.startswith('[SYSTEM NOTIFICATION') or '<task-notification>' in txt: continue
            if txt.startswith('Base directory for this skill:'):
                outl += [f"*Skill instructions loaded ({ts}); omitted.*", ""]; continue
            outl += [f"---", "", f"## User · {ts} UTC", "", red(txt), ""]
        elif role == 'user' and t == 'tool_result':
            txt = strip_reminders(result_text(b.get('content')))
            if txt: outl += ["<details><summary>Result</summary>", "", fence(red(short(txt))), "", "</details>", ""]
        elif role == 'assistant' and t == 'text' and b['text'].strip():
            outl += [f"### Claude · {ts} UTC", "", red(b['text'].strip()), ""]
        elif role == 'assistant' and t == 'tool_use':
            outl += ["> Tool call: " + red(tool_summary(b['name'], b.get('input', {}))).replace('\n', '\n> '), ""]
open(out, 'w').write('\n'.join(outl) + '\n')
print('lines', len(outl))
