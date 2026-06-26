# Day 1 · Demo 1 — Create and deploy an agent (Copilot Studio)

**Slide 56.** This is a **portal / natural-language** demo in Microsoft Copilot
Studio — there is no SDK or `az` step, so it lives here as a click-by-click
runbook. (It needs a Copilot Studio / Microsoft 365 environment, not the Azure
resources from `infra/`.)

## Scenario
Build an agent called **Copilot Studio Guide** that helps users learn Copilot
Studio, grounded in the official documentation.

## Steps
1. Sign in to **Copilot Studio** (`https://copilotstudio.microsoft.com`).
   You land on the Home page.
2. In the *"Describe your agent"* box, enter:
   > *Help users learn how to create agents with Copilot Studio.*
   (Up to 1,024 characters. If you don't see this box, your environment doesn't
   support NL creation — use **Create an agent** instead.)
3. Optionally adjust the primary **language**, **solution**, and **schema name**.
4. The AI generates a **name, description, and instructions**, and suggests
   triggers, channels, knowledge, and tools. Accept, ignore, or dismiss.
5. When provisioning finishes, the **Overview** page opens. Refine name /
   description / instructions as needed.
6. **Add knowledge:** in the *Knowledge* section, **Add** the suggestion for
   `https://learn.microsoft.com/copilot-studio` → **Add** → **Add to agent**.
7. **Test** in the test pane (e.g. *"How do I add a knowledge source?"*), refine,
   then **Publish** and pick a channel (Teams, web, etc.).

## Talking points while you click
- Three build modes: **natural language**, **visual canvas**, **code**.
- Knowledge sources span M365, Dataverse, Azure, public/enterprise websites,
  and SAP/Salesforce/ServiceNow connectors.
- The four core capabilities: Intelligent Control, Custom Functionality,
  Multimodal Experiences, Secure Scalability.

Reference: https://learn.microsoft.com/en-us/microsoft-copilot-studio/fundamentals-get-started
