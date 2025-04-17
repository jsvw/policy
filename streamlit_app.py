import streamlit as st
import openai
import random

st.set_page_config(page_title="Policy AI Roundtable", layout="wide")

# New real names for bots
avatars = {
    "John the Strategist": "🧠",
    "Jane the Financial Analyst": "💰",
    "Emma the People Manager": "❤️",
    "Leo the Legal Advisor": "⚖️",
    "Sam the Client Relationship Manager": "🤝",
    "Isla the Innovator": "🚀",
    "Ethan the Ethics Specialist": "🧭",
    "Mia the Moderator": "🎤",
    "Esmee the Infographic Designer": "🎨"
}

# Initialize OpenAI client (new 1.x interface)
client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

roles = {
    "John the Strategist": "You are John the Strategist. ONLY speak from your own perspective. Never refer to yourself as another agent. Respond to the discussion so far. Reference other agents by name if you agree or disagree. Do not repeat your earlier arguments unless refining or rebutting.",
    "Jane the Financial Analyst": "You are Jane the Financial Analyst. ONLY speak from your own perspective. Evaluate financial impact and cost-benefit of policy proposals. Reference other agents by name if you agree or disagree. Do not repeat your earlier arguments unless refining or rebutting.",
    "Emma the People Manager": "You are Emma the People Manager. ONLY speak from your own perspective. Focus on employee well-being, morale, and team dynamics. Reference other agents by name if you agree or disagree. Do not repeat your earlier arguments unless refining or rebutting.",
    "Leo the Legal Advisor": "You are Leo the Legal Advisor. ONLY speak from your own perspective. Cover legal, contractual, and compliance aspects. Reference other agents by name if you agree or disagree. Do not repeat your earlier arguments unless refining or rebutting.",
    "Sam the Client Relationship Manager": "You are Sam the Client Relationship Manager. ONLY speak from your own perspective. Assess client perception and concerns. Reference other agents by name if you agree or disagree. Do not repeat your earlier arguments unless refining or rebutting.",
    "Isla the Innovator": "You are Isla the Innovator. ONLY speak from your own perspective. Offer bold, future-forward solutions. Reference other agents by name if you agree or disagree. Do not repeat your earlier arguments unless refining or rebutting.",
    "Ethan the Ethics Specialist": "You are Ethan the Ethics Specialist. ONLY speak from your own perspective. Ensure fairness, inclusion, and transparency. Reference other agents by name if you agree or disagree. Do not repeat your earlier arguments unless refining or rebutting.",
    "Mia the Moderator": "You are Mia the Moderator. ONLY speak from your own perspective. Guide discussion, highlight conflicts, summarize who said what, and call on specific agents to respond.",
    "Esmee the Infographic Designer": "You are Esmee the Infographic Designer. Create a clear, visually appealing infographic that summarizes the policy and each agent's main arguments. Generate an image based on the discussion transcript."
}

urgency_keywords = {
    "Jane the Financial Analyst": ["cost", "budget", "money", "salary", "efficiency", "profit", "billable"],
    "Emma the People Manager": ["morale", "burnout", "well-being", "work-life", "happiness", "team"],
    "Leo the Legal Advisor": ["legal", "contract", "compliance", "law", "regulation", "risk"],
    "Sam the Client Relationship Manager": ["client", "customer", "trust", "delivery", "accessibility"],
    "Isla the Innovator": ["change", "innovation", "future", "technology", "new", "experiment"],
    "Ethan the Ethics Specialist": ["fairness", "equality", "inclusion", "bias", "equity", "justice"],
    "John the Strategist": ["goal", "strategy", "direction", "long-term", "mission"]
}

st.title("🤖 AI Policy Roundtable")
st.subheader("Simulate a conversation between AI agents to evaluate a company policy")

# Input field to capture the policy to discuss
policy = st.text_input("💬 What policy should be discussed?", "firing those who do not achieve the KPIs")

# Depth setting: number of agent interaction cycles per click
cycles = st.number_input("🔄 Number of interaction cycles per round", min_value=1, max_value=5, value=1, step=1)

# Initialize session state if it doesn't exist or policy changes
if "conversation" not in st.session_state or st.session_state.policy != policy:
    st.session_state.conversation = [
        {"role": "user", "content": f"The team is discussing the policy: '{policy}'\nBegin by sharing your perspective. Speak only if your expertise is relevant or you have something to challenge or clarify. Engage with each other and seek consensus."}
    ]
    st.session_state.agent_opinions = {name: "" for name in roles.keys()}
    st.session_state.history = []
    st.session_state.policy = policy

st.markdown("### 🧑‍💼 Agents")
cols = st.columns(4)
for i, name in enumerate(roles):
    with cols[i % 4]:
        st.markdown(f"{avatars[name]} **{name}**")
        if st.session_state.agent_opinions[name]:
            preview = st.session_state.agent_opinions[name][:200]
            if len(st.session_state.agent_opinions[name]) > 200:
                preview += "..."
            st.caption(preview)

# Round button triggers discussion
if st.button("▶️ Run Next Round"):
    agent_names = list(roles.keys())
    conversation = st.session_state.conversation
    agent_opinions = st.session_state.agent_opinions

    # Moderator speaks once if not yet
    if not any(msg["role"] == "assistant" and "Mia the Moderator" in msg["content"] for msg in conversation):
        try:
            mod_response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "system", "content": roles["Mia the Moderator"]}, *conversation]
            )
            mod_content = mod_response.choices[0].message.content
            conversation.append({"role": "assistant", "content": f"Mia the Moderator says:\n{mod_content}"})
            agent_opinions["Mia the Moderator"] = mod_content.strip()
        except Exception as e:
            st.error(f"Mia the Moderator error: {e}")

    # Run multiple cycles of agent responses for deeper dialogue
    for _ in range(cycles):
        recent_text = " ".join(msg["content"].lower() for msg in conversation[-10:])
        round_agents = []
        for name in agent_names:
            if name == "Mia the Moderator": continue
            keywords = urgency_keywords.get(name, [])
            if any(kw in recent_text for kw in keywords) or random.random() < 0.9:
                round_agents.append(name)
        random.shuffle(round_agents)
        for name in round_agents:
            try:
                summary = "Here's what others have said:\n\n"
                for other, opinion in agent_opinions.items():
                    if opinion and other != name:
                        snippet = opinion[:200] + ("..." if len(opinion)>200 else "")
                        summary += f"- {other} said: {snippet}\n"
                user_prompt = f"{summary}\nPlease respond with your unique perspective, referencing others where helpful. Do not repeat yourself."
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": roles[name]},
                        *conversation,
                        {"role": "user", "content": user_prompt}
                    ]
                )
                content = response.choices[0].message.content
                conversation.append({"role": "assistant", "content": f"{name} says:\n{content}"})
                agent_opinions[name] = content.strip()
            except Exception as e:
                st.warning(f"{name} error: {e}")

    st.session_state.conversation = conversation
    st.session_state.agent_opinions = agent_opinions

st.markdown("---")
st.markdown("### 🗣️ Conversation")
for msg in st.session_state.conversation:
    st.markdown(f"{msg['content']}")

# Final recommendation by Moderator
if st.button("🧾 Get Final Recommendation"):
    try:
        result = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": roles["Mia the Moderator"] + " Summarize the discussion above. Give a final recommendation: should the policy be implemented? What would be the consequences, risks, and benefits?"},
                *st.session_state.conversation
            ]
        )
        final_summary = result.choices[0].message.content
        st.markdown("### ✅ Final Recommendation")
        st.success(final_summary)
    except Exception as e:
        st.error(f"Final summary error: {e}")

# Esmee: generate infographic
if st.button("🎨 Generate Infographic"):
    try:
        # build summary prompt
        summary_text = f"Policy: {policy}\n\n"
        for name, opinion in st.session_state.agent_opinions.items():
            summary_text += f"{name}: {opinion}\n\n"
        # request infographic image
        img_resp = client.images.generate(
            prompt=f"Create a clear, engaging infographic summarizing this policy discussion and each agent's key points:\n{summary_text}",
            size="1024x768"
        )
        image_url = img_resp.data[0].url
        st.image(image_url, caption="Infographic by Esmee the Designer")
    except Exception as e:
        st.error(f"Esmee error: {e}")

# Download transcript
if st.download_button(
    "📥 Download Transcript",
    data="\n\n".join(msg["content"] for msg in st.session_state.conversation),
    file_name="policy_discussion_transcript.txt"
):
    st.success("Transcript ready!")
