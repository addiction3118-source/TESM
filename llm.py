# ─────────────────────────────────────────────────────────────
# llm.py — LLM-роутер с памятью диалога и контекстом серверов.
# ─────────────────────────────────────────────────────────────
import time

import streamlit as st

import config
from core import classify


def build_context():
    cache=st.session_state.get("server_cache",{})
    if not cache: return ""
    lines=["СОСТОЯНИЕ СЕРВЕРОВ:"]
    for name,s in cache.items():
        url=st.session_state.servers_dict.get(name,"")
        if s["online"]:
            ci=f" CPU={s['cpu']:.0f}% RAM={s['ram']:.0f}% Disk={s.get('disk',0):.0f}%" if s.get("cpu") is not None else ""
            w=" SSL ИСТЕКАЕТ!" if s.get("ssl_days",999)<config.SSL_WARN_DAYS else ""
            lines.append(f"- {name}({url}): ОНЛАЙН http={s['status_code']} ip={s['ip']} ssl={s['ssl_days']}д{w}{ci}")
        else:
            lines.append(f"- {name}({url}): ОФЛАЙН {s['message'][:40]}")
    op=[i for i in st.session_state.incidents if i["status"]=="open"]
    if op:
        lines.append(f"\nИНЦИДЕНТЫ ({len(op)}):")
        for i in op[:5]: lines.append(f"  [{i['severity'].upper()}] {i['server']}: {i['msg']}")
    return "\n".join(lines)


def _msgs(sys, prompt, history):
    m=[{"role":"system","content":sys}]
    for h in history[-10:]:
        if h.get("role") in ("user","assistant") and h.get("content"):
            m.append({"role":h["role"],"content":h["content"]})
    m.append({"role":"user","content":prompt})
    return m


def route_and_call(prompt, mode, use_history=True):
    keys=st.session_state.get("api_keys",{})
    if mode=="auto":
        task=classify(prompt); provider,model,label=config.ROUTING[task]
    else:
        provider=mode
        if provider=="groq": task=classify(prompt); model=config.ROUTING.get(task,config.ROUTING["general"])[1]; label=f"Groq/{model[:14]}"
        elif provider=="gemini": model,label,task=config.GEMINI_MODEL,config.GEMINI_LABEL,"general"
        elif provider=="openai": model,label,task=config.OPENAI_MODEL,config.OPENAI_LABEL,"general"
        else: return {"error":f"Неизвестный провайдер {provider}"}
    key=keys.get(provider,"")
    if not key: return {"error":f"Ключ {provider.upper()} не задан"}
    base=st.session_state.get("system_prompt","You are a helpful assistant.")
    ctx=build_context()
    system=(base+"\n\n"+ctx+"\n\nИспользуй данные о серверах. Отвечай на русском.") if ctx else base
    history=st.session_state.get("chat_messages",[]) if use_history else []
    try:
        t0=time.time()
        if provider=="groq":
            from groq import Groq
            r=Groq(api_key=key).chat.completions.create(model=model,max_tokens=4096,messages=_msgs(system,prompt,history))
            text=r.choices[0].message.content; inp,out=r.usage.prompt_tokens,r.usage.completion_tokens
        elif provider=="gemini":
            import google.generativeai as genai
            genai.configure(api_key=key)
            gm=genai.GenerativeModel(model,system_instruction=system)
            gh=[{"role":"model" if h["role"]=="assistant" else "user","parts":[h["content"]]}
                for h in history[-10:] if h.get("content")]
            chat=gm.start_chat(history=gh); r=chat.send_message(prompt)
            text=r.text; inp,out=len(prompt)//4,len(text)//4
        elif provider=="openai":
            from openai import OpenAI
            r=OpenAI(api_key=key).chat.completions.create(model=model,max_tokens=4096,messages=_msgs(system,prompt,history))
            text=r.choices[0].message.content; inp,out=r.usage.prompt_tokens,r.usage.completion_tokens
        return {"text":text,"label":label,"task":task,"inp":inp,"out":out,
                "latency":int((time.time()-t0)*1000),"error":""}
    except Exception as e:
        return {"error":f"API: {e}"}
