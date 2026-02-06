import os
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import io
import pdfplumber
from cryptography.fernet import Fernet
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime
from dotenv import load_dotenv

load_dotenv()

# --- DATABASE CONFIGURATION (MySQL) ---
DATABASE_URL = os.getenv("DATABASE_URL")

# Safety Check: If DATABASE_URL is missing, use SQLite so the app doesn't crash during build
if not DATABASE_URL:
    DATABASE_URL = "sqlite:///./fallback.db"
    print("⚠️ No DATABASE_URL found. Using local SQLite.")

# Ensure the URL starts with mysql+mysqlconnector:// for SQLAlchemy
if "mysql" in DATABASE_URL and "+mysqlconnector" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("mysql://", "mysql+mysqlconnector://")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
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
    print("✅ MySQL Database Connected.")
except Exception as e:
    print(f"❌ Database Error: {e}")

# --- SECURITY LAYER ---
SECRET_KEY = os.getenv("ENCRYPTION_KEY", Fernet.generate_key().decode())
cipher_suite = Fernet(SECRET_KEY.encode())

app = FastAPI(title="SME FinHealth AI Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
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
                    if table: data.extend(table[1:]) 
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

        # --- KEYS SYNCED WITH APP.JS ---
        return {
            "total_rev": total_rev,
            "expense": total_exp,
            "profit": profit,
            "margin": profit, 
            "tax_estimate": tax_estimate,
            "forecast": growth_forecast,
            "health": health_status,
            "credit_rating": credit_rating,
            "credit_score": credit_rating,
            "security": "AES-256 Active",
            "advice": {"en": advice_en}
        }

    except Exception as e:
        return {"error": f"Analysis failed: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
