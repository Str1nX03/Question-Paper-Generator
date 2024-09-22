from flask import Flask, render_template, request, send_file, redirect, url_for
import fitz  # PyMuPDF
import google.generativeai as gga  # Ensure to install the appropriate package
from fpdf import FPDF
import os
import stripe  # For Stripe payments
import json

app = Flask(__name__)

# Stripe API configuration (Use your actual secret key)
stripe.api_key = "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"

# Replace with your actual Google API key
gga.configure(api_key='AIzaSyC5BVYL55poCffhsWB034hQQnVB3X0wf-E')

def read_pdf_lines(file_path):
    pdf_document = fitz.open(file_path)
    lines = []
    for page in pdf_document:
        text = page.get_text("text")
        lines.extend(text.splitlines())
    pdf_document.close()
    return lines

def generate_questions(prompt):
    model = gga.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    return response.text

def save_question_paper_to_pdf(questions, file_name="question_paper.pdf"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    for question in questions:
        pdf.multi_cell(0, 10, txt=question)
    pdf.output(file_name)
    return file_name

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        uploaded_file = request.files['file']
        if uploaded_file and uploaded_file.filename.endswith('.pdf'):
            file_path = os.path.join("uploads", uploaded_file.filename)
            uploaded_file.save(file_path)
            lines = read_pdf_lines(file_path)
            topics = "\n".join(lines)

            prompt = f'''
                Instructions for Question Generation:

        You are a highly intelligent AI designed to create educational content. Your task is to generate thoughtful and varied questions based on the syllabus provided below. The questions should cover a range of difficulty levels (easy, medium, and hard) and different types (multiple choice, short answer, and essay questions). Ensure that the questions are clear, concise, and directly related to the syllabus content.

        Syllabus:{topics}

        Requirements:

            Generate a total of 5 questions from each Unit given in the syllabus.
            Question and serial number of question all should be in the same line.
            If any line exceeds the character limit of 100 characters, then continue the question in the next line so that the lines
            won't go outside the page.
            WARNING:- DO NOT GO ABOVE 80 CHARACTERS IN ONE GO IN A SINGLE LINE, CHANGE THE LINE WHENEVER YOU HIT 100 CHARACTER MARK.
            Ensure the questions vary in difficulty.
            Questions should encourage critical thinking and application of knowledge.

        End of Instructions.
            '''

            output = generate_questions(prompt)
            questions = output.split('\n')

            pdf_file = save_question_paper_to_pdf(questions)
            return send_file(pdf_file, as_attachment=True)

    return render_template("index.html")

@app.route("/process_payment", methods=["POST"])
def process_payment():
    try:
        # Create a Stripe Checkout Session
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': 'AI Question Paper Generator',
                        'description': 'Purchase to own the AI Question Paper Generator forever.',
                    },
                    'unit_amount': 1000,  # Amount in cents ($10.00)
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=url_for('success', _external=True) + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=url_for('index', _external=True),
        )
        return redirect(session.url, code=303)
    except Exception as e:
        return str(e)

@app.route("/success")
def success():
    return render_template("success.html")

if __name__ == "__main__":
    if not os.path.exists("uploads"):
        os.makedirs("uploads")
    app.run(debug=True)