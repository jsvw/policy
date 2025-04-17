import streamlit as st
import openai
import random
import requests
from io import BytesIO

st.set_page_config(page_title="Policy AI Roundtable", layout="wide")

# Avatars for bots
avatars = {
    "John the Strategist": "🧠",
    "Jane the Financial Analyst": "💰",
    "Emma the People Manager": "❤️",
    "Leo the Legal Advisor": "⚖️",
    "Sam the Client Relationship Manager": "🤝",
    "Isla the Innovator": "🚀",
    "Ethan the Ethics Specialist": "🧭",
    "Mia the Moderator": "🎤"
}

# Initialize OpenAI client
client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Define roles for discussion agents
roles = {
    "John the Strategist": "You are John the Strategist. ONLY speak from your own perspective. Never refer to yourself as another agent. Respond to the discussion so far. Reference other agents by name if you agree or disagree. Do not repeat your earlier arguments unless refining or rebutting.",
    "Jane the Financial Analyst": "You are Jane the Financial Analyst. ONLY speak from your own perspective. Evaluate financial impact and cost-benefit of policy proposals. Reference other agents by name if you agree or disagree. Do not repeat your earlier arguments unless refining or rebutting.",
    "Emma the People Manager": "You are Emma the People Manager. ONLY speak from your own perspective. Focus on employee well-being, morale, and team dynamics. Reference other agents by name if you agree or disagree. Do not repeat your earlier arguments unless refining or rebutting.",
    "Leo the Legal Advisor": "You are Leo the Legal Advisor. ONLY speak from your own perspective. Cover legal, contractual, and compliance aspects. Reference other agents by name if you agree or disagree. Do not repeat your earlier arguments unless refining or rebutting.",
    "Sam the Client Relationship Manager": "You are Sam the Client Relationship Manager. ONLY speak from your own perspective. Assess client perception and concerns. Reference other agents by name if you agree or disagree. Do not repeat your earlier arguments unless refining or rebutting.",
    "Isla the Innovator": "You are Isla the Innovator. ONLY speak from your own perspective. Offer bold, future-forward solutions. Reference other agents by name if you agree or disagree. Do not repeat your earlier arguments unless refining or rebutting.",
    "Ethan the Ethics Specialist": "You are Ethan the Ethics Specialist. ONLY speak from your own perspective. Ensure fairness, inclusion, and transparency. Reference other agents by name if you agree or disagree. Do not repeat your earlier arguments unless refining or rebutting.",
    "Mia the Moderator": "You are Mia the Moderator. ONLY speak from your own perspective. Guide discussion, highlight conflicts, summarize who said what, and call on specific agents to respond."
}

# Keywords to trigger agents
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

# Policy input
policy = st.text_input("💬 What policy should be discussed?", "firing those who do not achieve the KPIs")

# Depth: number of cycles per round
cycles = st.number_input("🔄 Number of interaction cycles per round", min_value=1, max_value=5, value=1, step=1)

# Initialize session state when policy changes
if "conversation" not in st.session_state or st.session_state.policy != policy:
    st.session_state.conversation = [
        {"role": "user", "content": f"The team is discussing the policy: '{policy}'\nBegin by sharing your perspective. Speak only if your expertise is relevant or you have something to challenge or clarify. Engage with each other and seek consensus."}
    ]
    st.session_state.agent_opinions = {name: "" for name in roles}
    st.session_state.policy = policy

# Display agents
st.markdown("### 🧑‍💼 Agents")
cols = st.columns(4)
for i, name in enumerate(roles):
    with cols[i % 4]:
        st.markdown(f"{avatars[name]} **{name}**")
        if st.session_state.agent_opinions[name]:
            snippet = st.session_state.agent_opinions[name][:200]
            if len(st.session_state.agent_opinions[name]) > 200:
                snippet += "..."
            st.caption(snippet)

# Run a round
if st.button("▶️ Run Next Round"):
    conversation = st.session_state.conversation
    agent_opinions = st.session_state.agent_opinions

    # Moderator first
    if not any(msg["role"] == "assistant" and "Mia the Moderator" in msg["content"] for msg in conversation):
        try:
            mod = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "system", "content": roles["Mia the Moderator"]}, *conversation]
            )
            text = mod.choices[0].message.content
            conversation.append({"role": "assistant", "content": f"Mia the Moderator says:\n{text}"})
            agent_opinions["Mia the Moderator"] = text.strip()
        except Exception as e:
            st.error(f"Mia the Moderator error: {e}")

    # Agent cycles
    for _ in range(cycles):
        recent = " ".join(m["content"].lower() for m in conversation[-10:])
        pool = []
        for name in roles:
            if name == "Mia the Moderator": continue
            kws = urgency_keywords.get(name, [])
            if any(k in recent for k in kws) or random.random() < 0.9:
                pool.append(name)
        random.shuffle(pool)
        for name in pool:
            try:
                summary = "Here's what others have said:\n\n"
                for other, opin in agent_opinions.items():
                    if opin and other != name:
                        snip = opin[:200] + ("..." if len(opin)>200 else "")
                        summary += f"- {other} said: {snip}\n"
                prompt = f"{summary}\nPlease respond with your unique perspective, referencing others where helpful. Do not repeat yourself."
                resp = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "system", "content": roles[name]}, *conversation, {"role": "user", "content": prompt}]
                )
                out = resp.choices[0].message.content
                conversation.append({"role": "assistant", "content": f"{name} says:\n{out}"})
                agent_opinions[name] = out.strip()
            except Exception as e:
                st.warning(f"{name} error: {e}")

    # Save state
    st.session_state.conversation = conversation
    st.session_state.agent_opinions = agent_opinions

st.markdown("---")

# Display conversation
st.markdown("### 🗣️ Conversation")
for msg in st.session_state.conversation:
    st.markdown(f"{msg['content']}")

# Final recommendation
if st.button("🧾 Get Final Recommendation"):
    try:
        fin = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": roles["Mia the Moderator"] + " Summarize the discussion above. Give a final recommendation: should the policy be implemented? What would be the consequences, risks, and benefits?"}, *st.session_state.conversation]
        )
        st.success(fin.choices[0].message.content)
    except Exception as e:
        st.error(f"Final summary error: {e}")

# Download transcript
transcript_data = "".join(m["content"] for m in st.session_state.conversation)
if st.download_button(
    "📥 Download Transcript",
    data=transcript_data,
    file_name="policy_discussion_transcript.txt"
):
    st.success("Transcript ready!")

# Visual summary of the discussion
if st.button("🖼️ Generate Visual Summary"):
    # Step 1: Generate a concise one-sentence summary
    try:
        summary_messages = [
            {"role": "system", "content": roles["Mia the Moderator"]},
            *st.session_state.conversation,
            {"role": "user", "content": "Please provide a one-sentence summary of the discussion above."}
        ]
        summary_resp = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=summary_messages,
            temperature=0.5,
            max_tokens=50
        )
        concise_summary = summary_resp.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"Summary generation error: {e}")
        concise_summary = None

    # Step 2: Create and display the infographic if summary succeeded
    if concise_summary:
        try:
            img_resp = client.images.generate(
                model="dall-e-3",
                prompt=f"A modern, clean, and visually engaging infographic without text, summarizing workplace policy discussions.: {concise_summary}",
                n=1,
                size="1024x1024"
            )
            image_url = img_resp.data[0].url
            st.image(image_url, caption="Visual Summary of Summary")

            # Button to download the generated image
            try:
                response = requests.get(image_url)
                img_bytes = BytesIO(response.content)
                st.download_button(
                    "📥 Download Image",
                    data=img_bytes,
                    file_name="visual_summary.png",
                    mime="image/png"
                )
            except Exception as e:
                st.error(f"Download image error: {e}")

        except Exception as e:
            st.error(f"Visual summary error: {e}")
