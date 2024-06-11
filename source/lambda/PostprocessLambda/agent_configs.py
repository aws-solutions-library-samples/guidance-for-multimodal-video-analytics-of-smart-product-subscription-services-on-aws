from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain.agents import AgentType, initialize_agent, load_tools

# --------XML Agent Prompt------
from langchain.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    PromptTemplate
)

template = '''You are a helpful assistant. Help the user answer any questions.

You have access to the following tools:

{tools}

In order to use a tool, you can use <tool></tool> and <tool_input></tool_input> tags. You will then get back a response in the form <observation></observation>
For example, if you have a tool called 'search' that could run a google search, in order to search for the weather in SF you would respond:

<tool>search</tool><tool_input>weather in SF</tool_input>
<observation>64 degrees</observation>

When you are done, respond with a final answer between <final_answer></final_answer>. For example:

<final_answer>The weather in SF is 64 degrees</final_answer>

Begin!

Previous Conversation:
{chat_history}

Question: {input}
{agent_scratchpad}'''

prompt_template = PromptTemplate(
    input_variables=["agent_scratchpad", "chat_history", "input", "tools"],
    template=template
)

human_message_prompt = HumanMessagePromptTemplate(
    prompt=prompt_template
)

prompt = ChatPromptTemplate(
    input_variables=["agent_scratchpad", "input", "tools"],
    partial_variables={"chat_history": ""},
    messages=[human_message_prompt]
)

# -----------Tools---------------------

tools = load_tools(
    ["awslambda", "sleep"],
    awslambda_tool_name="SMS-sender",
    awslambda_tool_description="sends an SMS message with the specified content to mobile phone",
    function_name="test_send_sms")

tools1 = load_tools(
    ["awslambda"],
    awslambda_tool_name="IoTCore-sender",
    awslambda_tool_description="sends an iot core message with the specified content to edge devices which usually in home or yard.",
    function_name="Cloud_To_Device_Notification",
)

tools2 = load_tools(
    ["awslambda"],
    awslambda_tool_name="Email-sender",
    awslambda_tool_description="sends an email with the specified content to test@testing123.com",
    function_name="SNS_Send_Notification",
)

tools.append(tools1[0])
tools.append(tools2[0])