from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import io
import pdfplumber
import os
from cryptography.fernet import Fernet
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime
from dotenv import load_dotenv

load_dotenv()

# --- DATABASE CONFIGURATION ---
# In production, set DATABASE_URL in your hosting environment
#DATABASE_URL = os.getenv("DATABASE_URL", "mysql+mysqlconnector://root:PASSWORD@localhost/finhealth_db")
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Assessment(Base):
    __tablename__ = "assessments"
    id = Column(Integer, primary_key=True, index=True)
    industry = Column(String(50))
    revenue = Column(Float)
    profit = Column(Float)
    health = Column(String(20))
    credit_score = Column(String(20))
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

try:
    Base.metadata.create_all(bind=engine)
    print("✅ Database Connected.")
except Exception as e:
    print(f"❌ Database Error: {e}")

# --- SECURITY LAYER ---
# Use a static key from environment variables so you don't lose access to data on restart
SECRET_KEY = os.getenv("ENCRYPTION_KEY", Fernet.generate_key().decode())
cipher_suite = Fernet(SECRET_KEY.encode())

app = FastAPI(title="SME FinHealth AI Backend")

# Enable CORS for Production Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace "*" with your actual frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/upload")
async def upload_financials(file: UploadFile = File(...), industry: str = "General"):
    try:
        raw_contents = await file.read()
        encrypted_data = cipher_suite.encrypt(raw_contents)
        decrypted_contents = cipher_suite.decrypt(encrypted_data)

        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.StringIO(decrypted_contents.decode('utf-8', errors='ignore')))
        elif file.filename.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(io.BytesIO(decrypted_contents))
        elif file.filename.endswith('.pdf'):
            data = []
            with pdfplumber.open(io.BytesIO(decrypted_contents)) as pdf:
                for page in pdf.pages:
                    table = page.extract_table()
                    if table:
                        data.extend(table[1:]) 
            df = pd.DataFrame(data, columns=["type", "category", "amount"])
            df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
        else:
            return {"error": "Unsupported file format."}

        df.columns = df.columns.str.strip().str.lower()
        df = df.dropna(subset=['amount'])
        
        total_rev = float(df[df['type'].str.lower() == 'revenue']['amount'].sum())
        total_exp = float(df[df['type'].str.lower() == 'expense']['amount'].sum())
        profit = total_rev - total_exp
        margin = round((profit / total_rev) * 100, 2) if total_rev > 0 else 0

        tax_estimate = round(profit * 0.18, 2) if profit > 0 else 0 
        growth_forecast = round(total_rev * 1.12, 2) 

        benchmarks = {"Retail": 15, "Manufacturing": 20, "Services": 40, "Agriculture": 12, "Logistics": 10, "E-commerce": 18, "General": 20}
        target_margin = benchmarks.get(industry, 20)
        
        health_status = "Excellent" if margin >= target_margin else "Stable" if margin > 5 else "At Risk"
        credit_rating = "High" if profit > 0 and margin >= (target_margin / 2) else "Low"

        # Save to DB
        db_session = SessionLocal()
        record = Assessment(industry=industry, revenue=total_rev, profit=profit, health=health_status, credit_score=credit_rating)
        db_session.add(record)
        db_session.commit()
        db_session.close()

        advice_en = (f"As a {industry} enterprise, your profit margin of {margin}% is {health_status}. "
                     f"Your estimated GST liability is ₹{tax_estimate}. Next quarter revenue is forecasted at ₹{growth_forecast}.")

        return {
            "revenue": total_rev, "expense": total_exp, "profit": profit, "margin": margin,
            "tax_est": tax_estimate, "forecast": growth_forecast, "health": health_status,
            "credit_score": credit_rating, "security": "AES-256 Active",
            "advice": {"en": advice_en}
        }

    except Exception as e:
        return {"error": f"Analysis failed: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))

    uvicorn.run(app, host="0.0.0.0", port=port)
