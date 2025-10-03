# AI Chaining Guide - Reťazenie úloh s AI

Tento dokument vysvetľuje ako reťaziť úlohy s AI asistentom a aké možnosti máš.

## 🎯 Čo je reťazenie úloh?

**Reťazenie úloh** (task chaining) znamená že AI asistent môže vykonať viacero akcií za sebou, pričom výsledok jednej akcie použije ako vstup pre ďalšiu.

**Príklad:**
```
Používateľ: "Nájdi všetky open issues v projekte SCRUM a prirad ich používateľovi John"
```

AI asistent:
1. **Vyhľadá issues** pomocou `search_issues` s JQL: `project = SCRUM AND status = Open`
2. **Pre každé issue** zavolá `assign_issue` s `assignee = john`
3. **Vráti súhrn** koľko issues bolo priradených

---

## 🔧 Ako to funguje v našom systéme?

### 1. **Function Calling (OpenAI / Google AI)**

Náš systém používa **Function Calling** - AI model rozhodne ktoré funkcie zavolať a v akom poradí.

**Architektúra:**
```
User Prompt
    ↓
AI Provider (Google AI / OpenAI)
    ↓
Function Calls (tool_calls)
    ↓
MCP Executor
    ↓
Jira Adapter
    ↓
Jira API
```

**Kód:**
```python
# orchestrator/ai_assistant_api.py

# 1. User prompt
response = await provider.chat(
    messages=messages,
    tools=MCP_TOOLS,
    system_message=system_message
)

# 2. Check if AI wants to call tools
if response.get("tool_calls"):
    tool_results = []
    
    # 3. Execute each tool call
    for tool_call in response["tool_calls"]:
        function_name = tool_call["function_name"]
        function_args = tool_call["arguments"]
        
        # 4. Execute MCP action
        result = await execute_mcp_action(function_name, function_args, tenant_id)
        
        tool_results.append({
            "tool_call_id": tool_call["tool_call_id"],
            "function_name": function_name,
            "result": result
        })
    
    return {
        "message": response["message"],
        "tool_calls": tool_results
    }
```

### 2. **Multi-step Chaining**

Ak chceš aby AI vykonalo viacero krokov za sebou, musíš:

**Variant A: Single-turn (jednoduchý)**
- AI rozhodne o všetkých krokoch naraz
- Vykoná všetky tool calls v jednom requeste
- **Výhoda:** Rýchle
- **Nevýhoda:** Nemôže reagovať na výsledky predchádzajúcich krokov

**Variant B: Multi-turn (pokročilý)**
- AI vykoná prvý krok
- Výsledok sa pridá do konverzácie
- AI rozhodne o ďalšom kroku na základe výsledku
- **Výhoda:** Flexibilné, môže reagovať na výsledky
- **Nevýhoda:** Pomalšie (viac API calls)

**Príklad multi-turn:**
```python
# orchestrator/ai_assistant_api.py

# Turn 1: Search issues
response1 = await provider.chat(
    messages=[{"role": "user", "content": "Nájdi open issues v SCRUM"}],
    tools=MCP_TOOLS
)

# Execute tool call
result1 = await execute_mcp_action("search_issues", {"jql": "project = SCRUM AND status = Open"})

# Turn 2: Assign issues based on search results
messages.append({"role": "assistant", "content": f"Našiel som {len(result1['issues'])} issues."})
messages.append({"role": "user", "content": "Prirad ich všetky Johnovi"})

response2 = await provider.chat(
    messages=messages,
    tools=MCP_TOOLS
)

# Execute tool calls for each issue
for issue in result1['issues']:
    await execute_mcp_action("assign_issue", {"issue_key": issue['key'], "assignee": "john"})
```

---

## 🚀 LangChain vs. Náš systém

### **Náš systém (Function Calling)**

**Výhody:**
- ✅ Jednoduchý, priamy prístup
- ✅ Žiadne extra dependencies
- ✅ Funguje s Google AI aj OpenAI
- ✅ Rýchle prototypovanie

**Nevýhody:**
- ❌ Musíš manuálne implementovať multi-turn chaining
- ❌ Žiadne built-in memory management
- ❌ Žiadne built-in error handling pre chains

### **LangChain**

**Výhody:**
- ✅ Built-in chaining patterns (Sequential, Parallel, Conditional)
- ✅ Memory management (ConversationBufferMemory, etc.)
- ✅ Error handling a retry logic
- ✅ Veľa ready-made tools a integrations
- ✅ Agents ktoré môžu rozhodovať o krokoch

**Nevýhody:**
- ❌ Extra dependency (veľká knižnica)
- ❌ Strmšia learning curve
- ❌ Niekedy over-engineered pre jednoduché use cases

---

## 📚 Kedy použiť LangChain?

### **Použiť LangChain ak:**

1. **Potrebuješ komplexné chains:**
   ```python
   from langchain.chains import SequentialChain
   
   # Chain 1: Search issues
   search_chain = LLMChain(llm=llm, prompt=search_prompt)
   
   # Chain 2: Analyze issues
   analyze_chain = LLMChain(llm=llm, prompt=analyze_prompt)
   
   # Chain 3: Assign issues
   assign_chain = LLMChain(llm=llm, prompt=assign_prompt)
   
   # Sequential chain
   overall_chain = SequentialChain(
       chains=[search_chain, analyze_chain, assign_chain],
       input_variables=["project_key"],
       output_variables=["assigned_issues"]
   )
   ```

2. **Potrebuješ memory management:**
   ```python
   from langchain.memory import ConversationBufferMemory
   
   memory = ConversationBufferMemory()
   
   # Conversation history sa automaticky ukladá
   chain = ConversationChain(llm=llm, memory=memory)
   ```

3. **Potrebuješ agents:**
   ```python
   from langchain.agents import initialize_agent, Tool
   
   tools = [
       Tool(name="Search", func=search_issues, description="Search Jira issues"),
       Tool(name="Assign", func=assign_issue, description="Assign issue to user"),
   ]
   
   agent = initialize_agent(tools, llm, agent="zero-shot-react-description")
   agent.run("Find all open issues and assign them to John")
   ```

### **Nepoužívať LangChain ak:**

1. **Máš jednoduché use cases** - Function calling stačí
2. **Chceš minimálne dependencies** - Náš systém je lightweight
3. **Potrebuješ rýchle prototypovanie** - Function calling je rýchlejší

---

## 🎨 Príklady reťazenia v našom systéme

### **Príklad 1: Sequential chaining (jednoduchý)**

```python
# User: "Nájdi všetky open issues v SCRUM a prirad ich Johnovi"

# AI rozhodne o krokoch:
# 1. search_issues(jql="project = SCRUM AND status = Open")
# 2. assign_issue(issue_key="SCRUM-1", assignee="john")
# 3. assign_issue(issue_key="SCRUM-2", assignee="john")
# ...

# Náš systém vykoná všetky tool calls za sebou
```

### **Príklad 2: Conditional chaining (pokročilý)**

```python
# User: "Nájdi všetky high priority issues a ak je ich viac ako 10, prirad ich Johnovi"

# Turn 1: Search
response1 = await provider.chat(
    messages=[{"role": "user", "content": "Nájdi všetky high priority issues v SCRUM"}],
    tools=MCP_TOOLS
)

# Execute search
result1 = await execute_mcp_action("search_issues", {"jql": "project = SCRUM AND priority = High"})

# Turn 2: Conditional logic
if len(result1['issues']) > 10:
    messages.append({"role": "assistant", "content": f"Našiel som {len(result1['issues'])} issues."})
    messages.append({"role": "user", "content": "Prirad ich všetky Johnovi"})
    
    response2 = await provider.chat(messages=messages, tools=MCP_TOOLS)
    
    # Execute assignments
    for issue in result1['issues']:
        await execute_mcp_action("assign_issue", {"issue_key": issue['key'], "assignee": "john"})
```

### **Príklad 3: Parallel chaining**

```python
# User: "Pridaj komentár do SCRUM-1, SCRUM-2 a SCRUM-3"

# AI rozhodne o paralelných tool calls:
tool_calls = [
    {"function_name": "add_comment", "arguments": {"issue_key": "SCRUM-1", "comment": "..."}},
    {"function_name": "add_comment", "arguments": {"issue_key": "SCRUM-2", "comment": "..."}},
    {"function_name": "add_comment", "arguments": {"issue_key": "SCRUM-3", "comment": "..."}},
]

# Execute all in parallel
import asyncio
results = await asyncio.gather(*[
    execute_mcp_action(tc["function_name"], tc["arguments"], tenant_id)
    for tc in tool_calls
])
```

---

## 🔮 Budúce rozšírenia

### **1. LangChain integrácia (optional)**

Ak by si chcel pridať LangChain:

```python
# orchestrator/ai_langchain.py

from langchain.chat_models import ChatOpenAI
from langchain.agents import initialize_agent, Tool
from langchain.memory import ConversationBufferMemory

def create_jira_agent(tenant_id: str):
    """Create LangChain agent for Jira."""
    
    # Define tools
    tools = [
        Tool(
            name="search_issues",
            func=lambda jql: execute_mcp_action("search_issues", {"jql": jql}, tenant_id),
            description="Search Jira issues using JQL"
        ),
        Tool(
            name="add_comment",
            func=lambda issue_key, comment: execute_mcp_action("add_comment", {"issue_key": issue_key, "comment": comment}, tenant_id),
            description="Add comment to Jira issue"
        ),
        # ... more tools
    ]
    
    # Create agent
    llm = ChatOpenAI(temperature=0)
    memory = ConversationBufferMemory(memory_key="chat_history")
    
    agent = initialize_agent(
        tools,
        llm,
        agent="conversational-react-description",
        memory=memory,
        verbose=True
    )
    
    return agent

# Usage
agent = create_jira_agent("demo")
result = agent.run("Find all open issues in SCRUM and assign them to John")
```

### **2. Custom chaining patterns**

```python
# orchestrator/ai_chains.py

class JiraChain:
    """Custom chaining for Jira operations."""
    
    def __init__(self, provider, tenant_id):
        self.provider = provider
        self.tenant_id = tenant_id
        self.history = []
    
    async def run(self, prompt: str):
        """Run chain with automatic multi-turn."""
        
        messages = [{"role": "user", "content": prompt}]
        max_turns = 5
        
        for turn in range(max_turns):
            response = await self.provider.chat(messages, MCP_TOOLS)
            
            if not response.get("tool_calls"):
                # No more tool calls, return final response
                return response["message"]
            
            # Execute tool calls
            for tool_call in response["tool_calls"]:
                result = await execute_mcp_action(
                    tool_call["function_name"],
                    tool_call["arguments"],
                    self.tenant_id
                )
                
                # Add result to history
                messages.append({
                    "role": "assistant",
                    "content": f"Executed {tool_call['function_name']}: {result}"
                })
            
            # Check if we should continue
            messages.append({
                "role": "user",
                "content": "Continue if needed, otherwise summarize results."
            })
        
        return "Max turns reached"

# Usage
chain = JiraChain(provider, "demo")
result = await chain.run("Find all open issues and assign them to John")
```

---

## 📖 Odporúčania

### **Pre jednoduché use cases:**
- ✅ Použi náš Function Calling systém
- ✅ Jednoduchý, rýchly, bez extra dependencies

### **Pre komplexné use cases:**
- ✅ Zvážiť LangChain
- ✅ Built-in patterns, memory, error handling
- ✅ Agents pre automatické rozhodovanie

### **Pre custom logic:**
- ✅ Implementuj vlastné chaining patterns
- ✅ Máš plnú kontrolu nad flow
- ✅ Môžeš kombinovať s LangChain

---

## 🎯 Záver

Náš systém používa **Function Calling** ktorý je:
- ✅ Jednoduchý a priamy
- ✅ Funguje s Google AI aj OpenAI
- ✅ Dostatočný pre väčšinu use cases

Ak potrebuješ komplexnejšie reťazenie, môžeš:
1. **Implementovať vlastné chaining patterns** (odporúčam pre začiatok)
2. **Pridať LangChain** (ak potrebuješ advanced features)

**Odporúčanie:** Začni s Function Calling, pridaj LangChain len ak to naozaj potrebuješ.

---

**Vytvoril:** AI Assistant  
**Dátum:** 2025-01-03  
**Verzia:** 1.0.0

