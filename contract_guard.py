import os
import sys
import google.generativeai as genai
from pypdf import PdfReader
from reportlab.pdfgen import canvas

# Try to import IPython for pretty output in Notebooks
try:
    from IPython.display import Markdown, display
    IN_NOTEBOOK = True
except ImportError:
    IN_NOTEBOOK = False

# --- CONFIGURATION ---
# 🛑 PASTE YOUR API KEY HERE OR SET ENV VARIABLE 'GOOGLE_API_KEY'
API_KEY = os.environ.get("GOOGLE_API_KEY", "PASTE_YOUR_KEY_HERE")
MODEL_NAME = "gemini-2.5-flash"

if API_KEY == "PASTE_YOUR_KEY_HERE":
    print("❌ ERROR: API Key missing. Please set GOOGLE_API_KEY environment variable or paste it in the script.")
    sys.exit(1)

genai.configure(api_key=API_KEY)

# --- HELPER FUNCTIONS ---
def smart_print(title, content):
    """Prints formatted text depending on whether we are in a Notebook or Terminal."""
    if IN_NOTEBOOK:
        display(Markdown(f"### {title}"))
        display(Markdown(content))
        display(Markdown("---"))
    else:
        print(f"\n[{title.upper()}]")
        print("=" * 40)
        print(content)
        print("-" * 40)

def create_test_pdf(filename="vendor_contract.pdf"):
    """Generates a dummy PDF with violations for testing."""
    c = canvas.Canvas(filename)
    c.drawString(100, 800, "VENDOR SERVICE AGREEMENT (DRAFT)")
    c.drawString(100, 750, "1. PAYMENT TERMS: Client shall pay invoices within Net 90 Days.")
    c.drawString(100, 725, "2. LIABILITY: Vendor liability shall not exceed $100 USD.")
    c.drawString(100, 700, "3. JURISDICTION: Governing law shall be Antarctica.")
    c.save()
    print(f"✅ Generated test contract: {filename}")
    return filename

def extract_text_from_pdf(pdf_path):
    """Reads text from a real PDF file."""
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        return f"Error reading PDF: {e}"

# --- AGENT CLASS ---
class SessionAgent:
    def __init__(self, name, instruction):
        self.name = name
        self.model = genai.GenerativeModel(
            model_name=MODEL_NAME,
            system_instruction=instruction
        )
        self.chat = self.model.start_chat(history=[])

    def ask(self, prompt):
        print(f"🤖 {self.name} is thinking...")
        try:
            response = self.chat.send_message(prompt)
            return response.text
        except Exception as e:
            return f"API Error: {e}"

# --- MAIN WORKFLOW ---
def run_contract_guard(pdf_path):
    print(f"🚀 Launching ContractGuard ({MODEL_NAME})...")

    # 1. Define The Rules
    playbook = """
    POLICY RULES:
    1. Payment: Must be Net-30 or Net-45. (Net-90 is a VIOLATION).
    2. Liability: Must be at least $10,000. ($100 is a VIOLATION).
    3. Jurisdiction: Must be USA. (Antarctica is a VIOLATION).
    """

    # 2. Initialize Agents
    analyst = SessionAgent("Analyst", "You are a Legal Analyst. Extract clauses verbatim.")
    compliance = SessionAgent("Compliance", f"You are a Compliance Officer. Auditing against:\n{playbook}")
    negotiator = SessionAgent("Negotiator", "You are a Legal Negotiator. Draft redlines and emails.")

    # 3. Execution
    print("\n📄 Processing PDF...")
    raw_text = extract_text_from_pdf(pdf_path)
    
    # Step A: Analyst
    extracted = analyst.ask(f"Extract Payment, Liability, and Jurisdiction clauses:\n{raw_text}")
    smart_print("Analyst Report", extracted)

    # Step B: Compliance
    report = compliance.ask(f"Audit these clauses:\n{extracted}")
    smart_print("Compliance Audit", report)

    # Step C: Negotiation (Conditional)
    if "VIOLATION" in report.upper():
        print("⚠️ Violations Detected. Starting Negotiation...")
        draft = negotiator.ask(f"Violations found:\n{report}\n\n1. Redline the clauses.\n2. Draft an email.")
        
        smart_print("Negotiation Package", draft)
        
        # Save Output
        with open("Negotiation_Draft.txt", "w") as f:
            f.write(draft)
        print("✅ Negotiation Draft saved to 'Negotiation_Draft.txt'")
    else:
        print("✅ Contract Approved.")

if __name__ == "__main__":
    # Ensure a file exists
    if not os.path.exists("vendor_contract.pdf"):
        create_test_pdf()
    
    run_contract_guard("vendor_contract.pdf")