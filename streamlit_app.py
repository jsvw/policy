import streamlit as st
import openai
import os
import random

st.set_page_config(page_title="Policy AI Roundtable", layout="wide")

# Avatar placeholders (replace with URLs or paths to images if needed)
avatars = {
    "StrategyBot": "🧠",
    "FinanceBot": "💰",
    "PeopleBot": "❤️",
    "LegalBot": "⚖️",
    "ClientBot": "🤝",
    "InnovatorBot": "🚀",
    "EthicsBot": "🧭",
    "ModeratorBot": "🎤"
}

# Set API key
openai.api_key = st.secrets["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"] if "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" in st.secrets else st.text_input("Enter your OpenAI API key", type="password")

# Agent personas
roles = {
    "StrategyBot": "You are StrategyBot. ONLY speak from your own perspective. Never refer to yourself as another agent. Respond to the discussion so far. Reference other agents by name if you agree or disagree. Do not repeat your earlier arguments unless refining or rebutting.",
    "FinanceBot": "You are FinanceBot. ONLY speak from your own perspective. Evaluate financial impact and cost-benefit of policy proposals. Reference other agents by name if you agree or disagree. Do not repeat your earlier arguments unless refining or rebutting.",
    "PeopleBot": "You are PeopleBot. ONLY speak from your own perspective. Focus on employee well-being, morale, and team dynamics. Reference other agents by name if you agree or disagree. Do not repeat your earlier arguments unless refining or rebutting.",
    "LegalBot": "You are LegalBot. ONLY speak from your own perspective. Cover legal, contractual, and compliance aspects. Reference other agents by name if you agree or disagree. Do not repeat your earlier arguments unless refining or rebutting.",
    "ClientBot": "You are ClientBot. ONLY speak from your own perspective. Assess client perception and concerns. Reference other agents by name if you agree or disagree. Do not repeat your earlier arguments unless refining or rebutting.",
    "InnovatorBot": "You are InnovatorBot. ONLY speak from your own perspective. Offer bold, future-forward solutions. Reference other agents by name if you agree or disagree. Do not repeat your earlier arguments unless refining or rebutting.",
    "EthicsBot": "You are EthicsBot. ONLY speak from your own perspective. Ensure fairness, inclusion, and transparency. Reference other agents by name if you agree or disagree. Do not repeat your earlier arguments unless refining or rebutting.",
    "ModeratorBot": "You are ModeratorBot. ONLY speak from your own perspective. Guide discussion, highlight conflicts, summarize who said what, and call on specific agents to respond."
}

urgency_keywords = {
    "FinanceBot": ["cost", "budget", "money", "salary", "efficiency", "profit", "billable"],
    "PeopleBot": ["morale", "burnout", "well-being", "work-life", "happiness", "team"],
    "LegalBot": ["legal", "contract", "compliance", "law", "regulation", "risk"],
    "ClientBot": ["client", "customer", "trust", "delivery", "accessibility"],
    "InnovatorBot": ["change", "innovation", "future", "technology", "new", "experiment"],
    "EthicsBot": ["fairness", "equality", "inclusion", "bias", "equity", "justice"],
    "StrategyBot": ["goal", "strategy", "direction", "long-term", "mission"]
}

st.title("🤖 AI Policy Roundtable")
st.subheader("Simulate a conversation between AI agents to evaluate a company policy")

policy = st.text_input("💬 What policy should be discussed?", "Introduce a 4-day workweek for all consulting teams, with no salary reduction.")

if "conversation" not in st.session_state:
    st.session_state.conversation = [
        {"role": "user", "content": f"The team is discussing the policy: '{policy}'\nBegin by sharing your perspective. Speak only if your expertise is relevant or you have something to challenge or clarify. Engage with each other and seek consensus."}
    ]
    st.session_state.agent_opinions = {name: "" for name in roles.keys()}
    st.session_state.history = []

# Display avatars and current opinion summary
st.markdown("### 🧑‍💼 Agents")
cols = st.columns(4)
for i, name in enumerate(roles):
    with cols[i % 4]:
        st.markdown(f"{avatars[name]} **{name}**")
        if st.session_state.agent_opinions[name]:
            st.caption(st.session_state.agent_opinions[name][:200] + ("..." if len(st.session_state.agent_opinions[name]) > 200 else ""))

# Run a discussion round
if st.button("▶️ Run Next Round"):
    agent_names = list(roles.keys())
    conversation = st.session_state.conversation
    agent_opinions = st.session_state.agent_opinions

    if not any([msg["role"] == "assistant" and "ModeratorBot" in msg["content"] for msg in conversation]):
        # Start with Moderator
        try:
            mod_response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "system", "content": roles["ModeratorBot"]}, *conversation]
            )
            mod_content = mod_response["choices"][0]["message"]["content"]
            conversation.append({"role": "assistant", "content": f"ModeratorBot says:\n{mod_content}"})
            agent_opinions["ModeratorBot"] = mod_content.strip()
        except Exception as e:
            st.error(f"ModeratorBot error: {e}")

    # Recent discussion context
    recent_text = " ".join([msg["content"].lower() for msg in conversation[-10:]])
    round_agents = []
    for name in agent_names:
        if name != "ModeratorBot":
            keywords = urgency_keywords.get(name, [])
            if any(word in recent_text for word in keywords) or random.random() < 0.5:
                round_agents.append(name)

    random.shuffle(round_agents)

    for name in round_agents:
        try:
            summary = "Here's what others have said:\n\n"
            for other_name, opinion in agent_opinions.items():
                if opinion and other_name != name:
                    summary += f"- {other_name} said: {opinion[:200]}...\n"

            user_prompt = f"{summary}\nPlease respond with your unique perspective, referencing others where helpful. Do not repeat yourself."

            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": roles[name]},
                    *conversation,
                    {"role": "user", "content": user_prompt}
                ]
            )
            content = response["choices"][0]["message"]["content"]
            conversation.append({"role": "assistant", "content": f"{name} says:\n{content}"})
            agent_opinions[name] = content.strip()
        except Exception as e:
            st.warning(f"{name} error: {e}")

    st.session_state.conversation = conversation
    st.session_state.agent_opinions = agent_opinions

# Show full conversation
st.markdown("---")
st.markdown("### 🗣️ Conversation")
for msg in st.session_state.conversation:
    st.markdown(f"{msg['content']}")

# Final summary
if st.button("🧾 Get Final Recommendation"):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": roles["ModeratorBot"] + " Summarize the discussion above. Give a final recommendation: should the policy be implemented? What would be the consequences, risks, and benefits?"},
                *st.session_state.conversation
            ]
        )
        final_summary = response["choices"][0]["message"]["content"]
        st.markdown("### ✅ Final Recommendation")
        st.success(final_summary)
    except Exception as e:
        st.error(f"Final summary error: {e}")

# Export
if st.download_button("📥 Download Transcript", data="\n\n".join([msg["content"] for msg in st.session_state.conversation]), file_name="policy_discussion_transcript.txt"):
    st.success("Transcript ready!")
