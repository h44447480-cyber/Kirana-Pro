# Kirana Inventory + Billing System - Fully Fixed + Multi-language + Icons
import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import os
from datetime import datetime
from fpdf import FPDF
from io import BytesIO
import json
from weasyprint import HTML , CSS
import tempfile
from groq import Groq
import seaborn as sns
import matplotlib.pyplot as plt
import squarify

# ----- Page Config -----
st.set_page_config(page_title="Sales Stock", layout="wide")

# Session state setup
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

# Password check
if not st.session_state["authenticated"]:
    st.title("🔐 Secure Kirana Pro")
    password = st.text_input("Enter Password:", type="password")
    if st.button("Unlock"):
        if password == st.secrets["APP_PASSWORD"]:
            st.session_state["authenticated"] = True
        else:
            st.warning("Incorrect password!")
    st.stop()  # Stop rendering the app until unlocked

# --- Main App starts here ---
# st.title("✨ Welcome to Kirana Pro")

# rest of your app code...


# ----- Language selection -----
language = st.sidebar.selectbox(
    "Choose Language: ",
    ["English", "Urdu", "German", "French", "Spanish", "Arabic"]
)

# Currency options with icons
currency_options = [
    "🟢 ₨ PKR",
    "🟡 € German Euro",
    "🔴 € French Euro",
    "🔵 € Spanish Euro",
    "⚫ ریال Arabic Riyal"
]

# Sidebar selection
selected_label = st.sidebar.selectbox("Select Currency:", currency_options)

# Extract clean currency name
currency = selected_label.split()[-2] + " " + selected_label.split()[-1] \
    if "Euro" in selected_label else selected_label.split()[-1]

# Clean names will now be:
# PKR, German Euro, French Euro, Spanish Euro, Arabic Riyal

# Conversion Rates (Base = PKR)
conversion_rates = {
    "PKR": 1,
    "German Euro": 1/350,
    "French Euro": 1/350,
    "Spanish Euro": 1/350,
    "Arabic Riyal": 0.087
}

# Currency Format Function
def format_currency(x):
    try:
        rate = conversion_rates.get(currency, 1)
        converted = float(x) * rate
        
        if currency == "PKR":
            return f"Rs {converted:,.2f}"
        elif currency in ["German Euro", "French Euro", "Spanish Euro"]:
            return f"€ {converted:,.2f}"
        elif currency == "Arabic Riyal":
            return f"﷼ {converted:,.2f}"
        else:
            return f"{converted:,.2f}"
    except:
        return str(x)


# AI ChatBot
client = Groq(api_key=st.secrets["GROQ_API_KEY"])
# ==== Sidebar Chatbot ====
st.sidebar.subheader("🧠 Personal Assistant")
# User input
user_msg = st.sidebar.text_input("Ask something…")
if st.sidebar.button("Send"):
    if user_msg.strip():
        # Single-turn chat (no history)
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": user_msg}]
        )
        bot_reply = response.choices[0].message.content
        # Display user and bot messages
        st.sidebar.write("🧑‍💻 You: " + user_msg)
        st.sidebar.write("🤖 Bot: " + bot_reply)


# ----- Setup -----
DB_PATH = "data/kirana.db"
INVOICE_DIR = "invoices"
LOGO_PATH = "assets/shop_logo.png"

os.makedirs("data", exist_ok=True)
os.makedirs(INVOICE_DIR, exist_ok=True)
os.makedirs("assets", exist_ok=True)

# ----- SQLite Connection -----
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
c = conn.cursor()

# ----- Translations -----
translations = {
    "Kirana POS": {
        "English":"Kirana POS", 
        "Urdu":"کرانہ POS", 
        "German":"Kirana POS", 
        "French": "Kirana POS", 
        "Spanish": "Kirana POS", 
        "Arabic": "كيران POS"
    },
    "Dashboard": {
        "English":"Dashboard", 
        "Urdu":"ڈیش بورڈ", 
        "German":"Dashboard", 
        "French": "Tableau de bord", 
        "Spanish": "Tablero", 
        "Arabic": "لوحة القيادة"
    },
    "Inventory": {
        "English":"Inventory", 
        "Urdu":"انوینٹری", 
        "German":"Inventar", 
        "French": "Inventaire", 
        "Spanish": "Inventario", 
        "Arabic": "المخزون"
    },
    "Billing / POS": {
        "English":"Billing / POS", 
        "Urdu":"بلنگ / POS", 
        "German":"Abrechnung / POS", 
        "French": "Facturation / POS", 
        "Spanish": "Facturación / POS", 
        "Arabic": "الفوترة / نقطة البيع"
    },
    "Sales Report": {
        "English":"Sales Report", 
        "Urdu":"سیلز رپورٹ", 
        "German":"Verkaufsbericht", 
        "French": "Rapport des ventes", 
        "Spanish": "Informe de ventas", 
        "Arabic": "تقرير المبيعات"
    },
    "Visualizations": {
    "English": "Visualizations",
    "Urdu": "بصری خاکے",
    "German": "Visualisierungen",
    "French": "Visualisations",
    "Spanish": "Visualizaciones",
    "Arabic": "الرسوم البيانية"
    },
    "Select Chart": {
    "English": "Select Chart",
    "Urdu": "چارٹ منتخب کریں",
    "German": "Diagramm auswählen",
    "French": "Sélectionner un graphique",
    "Spanish": "Seleccionar gráfico",
    "Arabic": "اختر المخطط"
    },
    "Histogram": {
    "English": "Histogram",
    "Urdu": "ہسٹگرام",
    "German": "Histogramm",
    "French": "Histogramme",
    "Spanish": "Histograma",
    "Arabic": "مدرج تكراري"
    },
    "Box Plot": {
    "English": "Box Plot",
    "Urdu": "باکس پلاٹ",
    "German": "Boxplot",
    "French": "Boîte à moustaches",
    "Spanish": "Diagrama de caja",
    "Arabic": "مخطط الصندوق"
    },
    "Area Chart": {
    "English": "Area Chart",
    "Urdu": "ایریا چارٹ",
    "German": "Flächendiagramm",
    "French": "Graphique en aires",
    "Spanish": "Gráfico de área",
    "Arabic": "مخطط المساحة"
    },
    "Donut Chart": {
    "English": "Donut Chart",
    "Urdu": "ڈونٹ چارٹ",
    "German": "Donut-Diagramm",
    "French": "Graphique en anneau",
    "Spanish": "Gráfico de dona",
    "Arabic": "مخطط الدونات"
    },
    "Bubble Chart": {
    "English": "Bubble Chart",
    "Urdu": "ببل چارٹ",
    "German": "Blasendiagramm",
    "French": "Graphique à bulles",
    "Spanish": "Gráfico de burbujas",
    "Arabic": "مخطط الفقاعات"
    },
    "Tree Map": {
    "English": "Tree Map",
    "Urdu": "ٹری میپ",
    "German": "Baumkarte",
    "French": "Carte arborescente",
    "Spanish": "Mapa de árbol",
    "Arabic": "خريطة شجرية"
    },
    "Bubble Chart (Qty vs Price with Size = Amount)": {
    "English": "Bubble Chart (Quantity vs Price with Size = Amount)",
    "Urdu": "ببل چارٹ (مقدار بمقابلہ قیمت، سائز = رقم)",
    "German": "Blasendiagramm (Menge vs Preis, Größe = Betrag)",
    "French": "Graphique à bulles (Quantité vs Prix, Taille = Montant)",
    "Spanish": "Gráfico de burbujas (Cantidad vs Precio, Tamaño = Monto)",
    "Arabic": "مخطط الفقاعات (الكمية مقابل السعر، الحجم = المبلغ)"
    },
    "Donut Chart of Top Products": {
    "English": "Donut Chart of Top Products",
    "Urdu": "بہترین مصنوعات کا ڈونٹ چارٹ",
    "German": "Donut-Diagramm der Top-Produkte",
    "French": "Graphique en anneau des meilleurs produits",
    "Spanish": "Gráfico de dona de los productos principales",
    "Arabic": "مخطط الدونات لأفضل المنتجات"
    },
    "Histogram (Price Distribution)": {
    "English": "Histogram (Price Distribution)",
    "Urdu": "ہسٹگرام (قیمت کی تقسیم)",
    "German": "Histogramm (Preisverteilung)",
    "French": "Histogramme (Répartition des prix)",
    "Spanish": "Histograma (Distribución de precios)",
    "Arabic": "مدرج تكراري (توزيع الأسعار)"
    },
    "Box Plot (Price Outliers)": {
    "English": "Box Plot (Price Outliers)",
    "Urdu": "باکس پلاٹ (قیمت کے آؤٹ لائرز)",
    "German": "Boxplot (Preis-Ausreißer)",
    "French": "Boîte à moustaches (Valeurs aberrantes de prix)",
    "Spanish": "Diagrama de caja (Valores atípicos del precio)",
    "Arabic": "مخطط الصندوق (القيم الشاذة للسعر)"
    },
    "Area Chart (Sales Over Time)": {
    "English": "Area Chart (Sales Over Time)",
    "Urdu": "ایریا چارٹ (وقت کے ساتھ فروخت)",
    "German": "Flächendiagramm (Verkäufe im Zeitverlauf)",
    "French": "Graphique en aires (Ventes dans le temps)",
    "Spanish": "Gráfico de área (Ventas a lo largo del tiempo)",
    "Arabic": "مخطط المساحة (المبيعات بمرور الوقت)"
    },
    "Tree Map of Top Products": {
    "English": "Tree Map of Top Products",
    "Urdu": "بہترین مصنوعات کی ٹری میپ",
    "German": "Baumkarte der Top-Produkte",
    "French": "Carte arborescente des meilleurs produits",
    "Spanish": "Mapa de árbol de los productos principales",
    "Arabic": "خريطة شجرية لأفضل المنتجات"
    },
    "Top Products (Horizontal Bar Chart)": {
    "English": "Top Products (Horizontal Bar Chart)",
    "Urdu": "سب سے بہترین مصنوعات (افقی بار چارٹ)",
    "German": "Top-Produkte (horizontales Balkendiagramm)",
    "French": "Meilleurs produits (diagramme à barres horizontal)",
    "Spanish": "Productos principales (gráfico de barras horizontal)",
    "Arabic": "أفضل المنتجات (مخطط شريطي أفقي)"
    },
    "Scatter Plot (Quantity vs Price)": {
    "English": "Scatter Plot (Quantity vs Price)",
    "Urdu": "اسکیٹر پلاٹ (مقدار بمقابلہ قیمت)",
    "German": "Streudiagramm (Menge vs Preis)",
    "French": "Diagramme de dispersion (Quantité vs Prix)",
    "Spanish": "Gráfico de dispersión (Cantidad vs Precio)",
    "Arabic": "مخطط مبعثر (الكمية مقابل السعر)"
    },

    "Violin Plot (Price Distribution)": {
    "English": "Violin Plot (Price Distribution)",
    "Urdu": "وائلن پلاٹ (قیمت کی تقسیم)",
    "German": "Violindiagramm (Preisverteilung)",
    "French": "Graphique en violon (Distribution des prix)",
    "Spanish": "Gráfico de violín (Distribución de precios)",
    "Arabic": "مخطط الكمان (توزيع الأسعار)"
    },
    "Correlation Heatmap": {
    "English": "Correlation Heatmap",
    "Urdu": "تعلقات کی ہیٹ میپ",
    "German": "Korrelations-Heatmap",
    "French": "Carte thermique des corrélations",
    "Spanish": "Mapa de calor de correlación",
    "Arabic": "خريطة الحرارة للترابط"
    },

    "Pie Chart of Top Products": {
    "English": "Pie Chart of Top Products",
    "Urdu": "بہترین مصنوعات کا پائی چارٹ",
    "German": "Kreisdiagramm der Top-Produkte",
    "French": "Diagramme circulaire des meilleurs produits",
    "Spanish": "Gráfico circular de los productos principales",
    "Arabic": "مخطط دائري لأفضل المنتجات"
    },
    "Quantity": {
    "English": "Quantity",
    "Urdu": "مقدار",
    "German": "Menge",
    "French": "Quantité",
    "Spanish": "Cantidad",
    "Arabic": "الكمية"
    },
    "Price": {
    "English": "Price",
    "Urdu": "قیمت",
    "German": "Preis",
    "French": "Prix",
    "Spanish": "Precio",
    "Arabic": "السعر"
    },
    "WelcomeTitle": {
    "English": "✨ Welcome to Kirana Pro",
    "Urdu": "✨ Kirana Pro میں خوش آمدید",
    "German": "✨ Willkommen bei Kirana Pro",
    "French": "✨ Bienvenue sur Kirana Pro",
    "Spanish": "✨ Bienvenido a Kirana Pro",
    "Arabic": "✨ مرحبًا بك في Kirana Pro"
    },
    "No sales data to visualize.": {
    "English": "No sales data to visualize.",
    "Urdu": "کوئی سیل ڈیٹا موجود نہیں ہے۔",
    "German": "Keine Verkaufsdaten zur Visualisierung.",
    "French": "Aucune donnée de vente à visualiser.",
    "Spanish": "No hay datos de ventas para visualizar.",
    "Arabic": "لا توجد بيانات مبيعات للعرض."
    },
    "From": {
    "English": "From",
    "Urdu": "سے",
    "German": "Von",
    "French": "De",
    "Spanish": "Desde",
    "Arabic": "من"
    },
    "To": {
    "English": "To",
    "Urdu": "تک",
    "German": "À",
    "French": "À",
    "Spanish": "Hasta",
    "Arabic": "إلى"
    },
    "Sales Over Time": {
    "English": "Sales Over Time",
    "Urdu": "وقت کے ساتھ فروخت",
    "German": "Verkäufe im Zeitverlauf",
    "French": "Ventes au fil du temps",
    "Spanish": "Ventas a lo largo del tiempo",
    "Arabic": "المبيعات حسب الوقت"
    },
    "Top Selling Products": {
    "English": "Top Selling Products",
    "Urdu": "زیادہ فروخت ہونے والی مصنوعات",
    "German": "Meistverkaufte Produkte",
    "French": "Produits les plus vendus",
    "Spanish": "Productos más vendidos",
    "Arabic": "أفضل المنتجات مبيعًا"
    },
    "Could not parse items_json": {
    "English": "Could not parse items_json",
    "Urdu": "آئٹمز JSON کو پڑھا نہیں جا سکا",
    "German": "items_json konnte nicht verarbeitet werden",
    "French": "Impossible d'analyser items_json",
    "Spanish": "No se pudo analizar items_json",
    "Arabic": "تعذر解析 items_json"
    },
    "No product data found.": {
    "English": "No product data found.",
    "Urdu": "کوئی پراڈکٹ ڈیٹا نہیں ملا۔",
    "German": "Keine Produktdaten gefunden.",
    "French": "Aucune donnée produit trouvée.",
    "Spanish": "No se encontraron datos de productos.",
    "Arabic": "لم يتم العثور على بيانات المنتجات."
    },
    "Data Import/Export": {
        "English":"Data Import/Export", 
        "Urdu":"ڈیٹا درآمد/برآمد", 
        "German":"Daten Import/Export", 
        "French": "Import/Export de données", 
        "Spanish": "Importación/Exportación de datos", 
        "Arabic": "استيراد/تصدير البيانات"
    },
    "Help": {
        "English":"Help", 
        "Urdu":"مدد", 
        "German":"Hilfe", 
        "French": "Aide", 
        "Spanish": "Ayuda", 
        "Arabic": "مساعدة"
    },
    "Add Product": {
        "English":"Add Product ➕", 
        "Urdu":"مصنوعات شامل کریں ➕", 
        "German":"Produkt hinzufügen ➕", 
        "French": "Ajouter un produit ➕", 
        "Spanish": "Agregar producto ➕", 
        "Arabic": "أضف منتج ➕"
    },
    "Customer Name": {
        "English":"Customer name (optional)", 
        "Urdu":"صارف کا نام (اختیاری)", 
        "German":"Kundenname (optional)", 
        "French": "Nom du client (optionnel)", 
        "Spanish": "Nombre del cliente (opcional)", 
        "Arabic": "اسم العميل (اختياري)"
    },
    "Payment Method": {
        "English":"Payment method", 
        "Urdu":"ادائیگی کا طریقہ", 
        "German":"Zahlungsmethode", 
        "French": "Mode de paiement", 
        "Spanish": "Método de pago", 
        "Arabic": "طريقة الدفع"
    },
    "Notes": {
        "English":"Notes (optional)", 
        "Urdu":"نوٹس (اختیاری)", 
        "German":"Notizen (optional)", 
        "French": "Notes (optionnel)", 
        "Spanish": "Notas (opcional)", 
        "Arabic": "ملاحظات (اختياري)"
    },
    "Stock": {
        "English":"Stock", 
        "Urdu":"اسٹاک", 
        "German":"Bestand", 
        "French": "Stock", 
        "Spanish": "Inventario", 
        "Arabic": "المخزون"
    },
    "Total Sales": {
        "English":"Total Sales", 
        "Urdu":"کل فروخت", 
        "German":"Gesamtverkauf", 
        "French": "Ventes totales", 
        "Spanish": "Ventas totales", 
        "Arabic": "إجمالي المبيعات"
    },
    "Cart": {
        "English":"Cart", 
        "Urdu":"کارٹ", 
        "German":"Warenkorb", 
        "French": "Panier", 
        "Spanish": "Carrito", 
        "Arabic": "عربة التسوق"
    },
    "Complete Sale": {
        "English":"Complete Sale ✅", 
        "Urdu":"سیل مکمل کریں ✅", 
        "German":"Verkauf abschließen ✅", 
        "French": "Vente terminée ✅", 
        "Spanish": "Venta completada ✅", 
        "Arabic": "اكتمال البيع ✅"
    },
    "Search Product": {
        "English":"Search product name or barcode", 
        "Urdu":"مصنوعات کا نام یا بارکوڈ تلاش کریں", 
        "German":"Produktname oder Barcode suchen", 
        "French": "Rechercher produit ou code-barres", 
        "Spanish": "Buscar producto o código", 
        "Arabic": "ابحث عن المنتج أو الباركود"
    },
    "Delete Product": {
        "English":"Delete", 
        "Urdu":"حذف کریں", 
        "German":"Löschen", 
        "French": "Supprimer", 
        "Spanish": "Eliminar", 
        "Arabic": "حذف"
    },
    "No Products": {
        "English":"No products in inventory.", 
        "Urdu":"انوینٹری میں کوئی مصنوعات نہیں۔", 
        "German":"Keine Produkte im Inventar.", 
        "French": "Aucun produit en stock.", 
        "Spanish": "No hay productos en inventario.", 
        "Arabic": "لا توجد منتجات في المخزون."
    },
    "No Sales": {
        "English":"No sales yet.", 
        "Urdu":"ابھی تک کوئی فروخت نہیں ہوئی۔", 
        "German":"Noch keine Verkäufe.", 
        "French": "Aucune vente pour le moment.", 
        "Spanish": "No hay ventas todavía.", 
        "Arabic": "لا توجد مبيعات حتى الآن."
    },
    "Low Stock Threshold": {
        "English":"Low stock threshold", 
        "Urdu":"کم اسٹاک حد", 
        "German":"Niedriges Bestandslimit", 
        "French": "Seuil de stock faible", 
        "Spanish": "Umbral de stock bajo", 
        "Arabic": "حد المخزون المنخفض"
    },
    "Cart Empty": {
        "English":"Cart is empty. Add products from left.", 
        "Urdu":"کارٹ خالی ہے۔ بائیں جانب سے مصنوعات شامل کریں۔", 
        "German":"Warenkorb ist leer. Produkte von links hinzufügen.", 
        "French": "Le panier est vide. Ajoutez des produits à gauche.", 
        "Spanish": "El carrito está vacío. Agregue productos desde la izquierda.", 
        "Arabic": "السلة فارغة. أضف المنتجات من اليسار."
    },
    "Subtotal": {
        "English":"Subtotal", 
        "Urdu":"ذیلی کل", 
        "German":"Zwischensumme", 
        "French": "Sous-total", 
        "Spanish": "Subtotal", 
        "Arabic": "المجموع الجزئي"
    },
    "Discount": {
        "English":"Discount", 
        "Urdu":"رعایت", 
        "German":"Rabatt", 
        "French": "Remise", 
        "Spanish": "Descuento", 
        "Arabic": "خصم"
    },
    "Total": {
        "English":"Total", 
        "Urdu":"کل", 
        "German":"Gesamt", 
        "French": "Total", 
        "Spanish": "Total", 
        "Arabic": "الإجمالي"
    },
    "Notes Label": {
        "English":"Notes", 
        "Urdu":"نوٹس", 
        "German":"Notizen", 
        "French": "Notes", 
        "Spanish": "Notas", 
        "Arabic": "ملاحظات"
    },
    "Download Invoice PDF": {
        "English":"⬇ Download Invoice (PDF)", 
        "Urdu":"⬇ انوائس ڈاؤن لوڈ کریں (PDF)", 
        "German":"⬇ Rechnung herunterladen (PDF)", 
        "French": "⬇ Télécharger la facture (PDF)", 
        "Spanish": "⬇ Descargar factura (PDF)", 
        "Arabic": "⬇ تحميل الفاتورة (PDF)"
    },
    "Download Invoice HTML": {
        "English":"⬇ Download Invoice (HTML)", 
        "Urdu":"⬇ انوائس ڈاؤن لوڈ کریں (HTML)", 
        "German":"⬇ Rechnung herunterladen (HTML)", 
        "French": "⬇ Télécharger la facture (HTML)", 
        "Spanish": "⬇ Descargar factura (HTML)", 
        "Arabic": "⬇ تحميل الفاتورة (HTML)"
    },
    "Download Items CSV": {
        "English":"⬇ Download Items CSV", 
        "Urdu":"⬇ اشیاء CSV ڈاؤن لوڈ کریں", 
        "German":"⬇ Artikel CSV herunterladen", 
        "French": "⬇ Télécharger les articles CSV", 
        "Spanish": "⬇ Descargar artículos CSV", 
        "Arabic": "⬇ تحميل العناصر CSV"
    },
}


def tr(key):
    return translations.get(key, {}).get(language, key)

st.title(tr("WelcomeTitle"))

# ----- Create Tables -----
c.execute('''
CREATE TABLE IF NOT EXISTS products(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    barcode TEXT,
    name TEXT,
    category TEXT,
    cost_price REAL,
    sale_price REAL,
    stock REAL
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS sales(
    sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    total_amount REAL,
    items_json TEXT,
    payment_method TEXT,
    customer TEXT,
    notes TEXT
)
''')
conn.commit()

# ----- Helper Functions -----
def fetch_products():
    try:
        return pd.read_sql("SELECT * FROM products", conn)
    except:
        return pd.DataFrame(columns=['id','barcode','name','category','cost_price','sale_price','stock'])

def fetch_sales():
    try:
        return pd.read_sql("SELECT * FROM sales", conn)
    except:
        return pd.DataFrame(columns=['sale_id','date','total_amount','items_json','payment_method','customer','notes'])





def generate_invoice_pdf(sale_id, items, total, discount, customer="", payment_method="Cash", notes=""):
    """
    Generate invoice PDF using WeasyPrint (supports Unicode fully).
    Returns: Path to the generated PDF.
    """
    # Create HTML content
    items_rows = ""
    for item in items:
        name = str(item.get('name', ''))[:40]
        qty = int(item.get('qty', 0))
        price = float(item.get('price', 0.0))
        line_total = price * qty
        items_rows += f"""
        <tr>
            <td>{name}</td>
            <td style="text-align:center">{qty}</td>
            <td style="text-align:right">{price:.2f}</td>
            <td style="text-align:right">{line_total:.2f}</td>
        </tr>
        """

    logo_html = ""
    if os.path.exists(LOGO_PATH):
        logo_html = f'<img src="{LOGO_PATH}" style="width:100px; float:right;">'

    html_content = f"""
    <html>
    <head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; font-size: 12px; }}
        table {{ border-collapse: collapse; width: 100%; margin-top: 10px; }}
        th, td {{ border: 1px solid #333; padding: 5px; }}
        th {{ background-color: #f2f2f2; }}
        h1 {{ text-align: center; }}
    </style>
    </head>
    <body>
        {logo_html}
        <h1>Shop Invoice</h1>
        <p><strong>Invoice ID:</strong> {sale_id}</p>
        <p><strong>Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        {"<p><strong>Customer:</strong> "+customer+"</p>" if customer else ""}
        <p><strong>Payment Method:</strong> {payment_method}</p>

        <table>
            <tr>
                <th>{tr('Add Product')}</th>
                <th>Qty</th>
                <th>{tr('Total')}</th>
                <th>{tr('Subtotal')}</th>
            </tr>
            {items_rows}
        </table>

        <p><strong>{tr('Discount')}:</strong> {format_currency(discount)}</p>
        <p><strong>{tr('Total')}:</strong> {format_currency(total)}</p>
        {"<p><strong>"+tr('Notes Label')+":</strong> "+notes+"</p>" if notes else ""}
    </body>
    </html>
    """

    # Save PDF to invoices folder
    invoice_file = os.path.join(INVOICE_DIR, f"invoice_{sale_id}.pdf")
    HTML(string=html_content).write_pdf(invoice_file)

    return invoice_file


# ----- Sidebar -----
st.sidebar.title(tr("🏪 Kirana Pro"))
page = st.sidebar.radio(
    "🧭 Navigation",
    [
        "📊 " + tr("Dashboard"),
        "📦 " + tr("Inventory"),
        "🧾 " + tr("Billing / POS"),
        "📑 " + tr("Sales Report"),
        "📈 " + tr("Visualizations"),
        "🔄 " + tr("Data Import/Export"),
        "❓ " + tr("Help")
    ]
)

# ----- Pages -----
if page.startswith("📊"):
    st.title("📈 " + tr("Dashboard"))

    # ---- Fetch data ----
    products_df = fetch_products()
    sales_df = fetch_sales()
    today = datetime.now().date()

    # ----- Metrics ----
    if not sales_df.empty:
        # Safe date parsing
        sales_df['date_parsed'] = pd.to_datetime(sales_df['date'], errors='coerce').dt.date
        # Ensure numeric total_amount
        sales_df['total_amount'] = pd.to_numeric(sales_df['total_amount'], errors='coerce').fillna(0)
    
        today_sales = sales_df[sales_df['date_parsed'] == today]
        total_today = today_sales['total_amount'].sum() if not today_sales.empty else 0
        total_sales = sales_df['total_amount'].sum()
    else:
        total_today = 0
        total_sales = 0

    # Inventory metric
    inventory_count = len(products_df)

    # Safe Stock calculation
    try:
        if not products_df.empty:
            stock_safe = pd.to_numeric(products_df['stock'], errors='coerce').fillna(0)
            cost_safe = pd.to_numeric(products_df['cost_price'], errors='coerce').fillna(0)
            total_stock = (stock_safe * cost_safe).sum()
        else:
            total_stock = 0
    except:
        total_stock = 0

    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(tr("Total Sales Today"), format_currency(total_today))
    col2.metric(tr("Inventory"), inventory_count)
    col3.metric(tr("Stock"), format_currency(total_stock))
    col4.metric(tr("Total Sales Count"), len(sales_df))

    # ----- Recent Sales Section -----
    st.markdown("### Recent Sales")
    if not sales_df.empty:
        if "recent_sales" not in st.session_state:
            st.session_state.recent_sales = sales_df.sort_values("date", ascending=False).head(100).copy()

        updated_sales = st.session_state.recent_sales.copy()
        deleted = False  # track if a row is deleted

        for i, row in updated_sales.iterrows():
            sale_id = row['sale_id']
            with st.expander(f"{i+1}. 📅 {row.get('date','')} | 👤 {row.get('customer','')} | 💰 {format_currency(row.get('total_amount',0))}"):
                st.write("**👤 Customer:**", row.get('customer',''))
                st.write("**💰 Total Amount:**", format_currency(row.get('total_amount',0)))
                st.write("**💳 Payment:**", row.get('payment_method',''))
                st.write("**📝 Notes:**", row.get('notes',''))

                # Delete button
                if st.button("❌ Delete", key=f"delete_sale_{sale_id}"):
                    try:
                        c.execute("DELETE FROM sales WHERE sale_id=?", (sale_id,))
                        conn.commit()
                        st.success(f"Sale ID {sale_id} deleted!")

                        # Remove deleted row from session_state
                        st.session_state.recent_sales = st.session_state.recent_sales[
                            st.session_state.recent_sales['sale_id'] != sale_id
                        ]
                        deleted = True  # mark deletion happened

                    except Exception as e:
                        st.error(f"Error deleting sale: {e}")

        # If a deletion happened, rerun the script by using session_state trigger
        if deleted:
            # Increment counter to force refresh logic if needed
            st.session_state.refresh_counter = st.session_state.get("refresh_counter", 0) + 1
            # Stop current run; Streamlit will rerun automatically
            st.stop()
        # Show message if empty
        if st.session_state.recent_sales.empty:
            st.info(tr("No Sales"))
    else:
        st.info(tr("No Sales"))


elif page.startswith("📦"):
    st.title("🗂️ " + tr("Inventory"))

    # Fetch products
    products_df = fetch_products()

    # ----- Add Product Form -----
    st.markdown("#### " + tr("Add Product"))
    with st.form("add_product", clear_on_submit=True):
        name = st.text_input(tr("Add Product"))
        barcode = st.text_input("Barcode (optional)")
        category = st.text_input("Category","General")
        cost_price = st.number_input("Cost price",0.0,format="%.2f")
        sale_price = st.number_input("Sale price",0.0,format="%.2f")
        stock = st.number_input("Stock quantity",0.0,format="%.2f")
        submitted = st.form_submit_button(tr("Add Product"))
        if submitted:
            c.execute(
                "INSERT INTO products (barcode,name,category,cost_price,sale_price,stock) VALUES (?,?,?,?,?,?)",
                (barcode or "", name, category, float(cost_price), float(sale_price), float(stock))
            )
            conn.commit()
            st.success(f"{tr('Add Product')} '{name}' added!")

    # ----- Product List -----
    st.markdown("#### Product List")
    products_df = fetch_products()

    if not products_df.empty:
        if "inventory_products" not in st.session_state:
            st.session_state.inventory_products = products_df.copy()

        updated_products = st.session_state.inventory_products.copy()
        deleted = False

        for i, row in updated_products.iterrows():
            product_id = row['id']  # Assuming 'id' is primary key
            with st.expander(f"{i+1}. {row.get('name','')} | Category: {row.get('category','')} | Stock: {row.get('stock',0)}"):
                st.write("**Barcode:**", row.get('barcode',''))
                st.write("**Cost Price:**", row.get('cost_price',0.0))
                st.write("**Sale Price:**", row.get('sale_price',0.0))
                st.write("**Stock:**", row.get('stock',0))

                # ----- Delete Button -----
                if st.button("❌ Delete", key=f"delete_product_{product_id}"):
                    try:
                        c.execute("DELETE FROM products WHERE id=?", (product_id,))
                        conn.commit()
                        st.success(f"Product '{row.get('name','')}' deleted!")

                        # Update session_state
                        st.session_state.inventory_products = st.session_state.inventory_products[
                            st.session_state.inventory_products['id'] != product_id
                        ]
                        deleted = True

                    except Exception as e:
                        st.error(f"Error deleting product: {e}")

        # Refresh UI safely
        if deleted:
            st.stop()

        if st.session_state.inventory_products.empty:
            st.info(tr("No Products"))
    else:
        st.info(tr("No Products"))


elif page.startswith("🧾"):
    st.title("💳 " + tr("Billing / POS"))
    products_df = fetch_products()
    if 'cart' not in st.session_state:
        st.session_state.cart=[]
    cart = st.session_state.cart
    col1,col2 = st.columns([2,1])
    with col1:
        q = st.text_input(tr("Search Product"))
        filtered = products_df.copy() if 'products_df' in locals() else fetch_products()
        if q:
            filtered = filtered[filtered['name'].str.contains(q,case=False,na=False) | filtered['barcode'].astype(str).str.contains(q, na=False)]
        if not filtered.empty:
            option = st.selectbox(tr("Add Product"), options=filtered['id'].tolist(), format_func=lambda x: f"{filtered.loc[filtered['id']==x,'name'].values[0]} (Stock: {filtered.loc[filtered['id']==x,'stock'].values[0]})")
            qty = st.number_input("Quantity",1,step=1)
            if st.button("➕ Add to Cart"):
                prod = filtered[filtered['id']==option].iloc[0]
                cart.append({"id":int(prod['id']),"name":prod['name'],"qty":qty,"price":float(prod['sale_price'])})
                st.success(f"{prod['name']} x{qty} added!")
        else:
            st.info(tr("No Products"))

    with col2:
        st.markdown("#### " + tr("Cart"))
        if cart:
            cart_df = pd.DataFrame(cart)
            cart_df["line_total"] = cart_df["qty"]*cart_df["price"]
            st.table(cart_df[["name","qty","price","line_total"]])
            subtotal = cart_df["line_total"].sum()
            discount_p = st.number_input(tr("Discount")+" %",0.0,100.0)
            discount_amt = subtotal*(discount_p/100)
            total = subtotal - discount_amt
            st.write(tr("Subtotal")+":", format_currency(subtotal))
            st.write(tr("Discount")+":", format_currency(discount_amt))
            st.write(tr("Total")+":", format_currency(total))
            customer = st.text_input(tr("Customer Name"))
            payment_method = st.selectbox(tr("Payment Method"), ["Cash","Card","Mobile"])
            notes = st.text_area(tr("Notes"))
            if st.button(tr("Complete Sale")):
                # Deduct stock
                products_dict = fetch_products().set_index('id').to_dict('index')
                ok=True
                for item in cart:
                    pid=item['id']
                    if float(products_dict[pid]['stock'])<item['qty']:
                        st.error(f"Not enough stock for {products_dict[pid]['name']}")
                        ok=False
                        break
                if ok:
                    for item in cart:
                        pid=item['id']
                        new_stock = float(products_dict[pid]['stock']) - item['qty']
                        c.execute("UPDATE products SET stock=? WHERE id=?",(new_stock,pid))
                    conn.commit()
                    c.execute("INSERT INTO sales (date,total_amount,items_json,payment_method,customer,notes) VALUES (?,?,?,?,?,?)",
                              (datetime.now().strftime("%Y-%m-%d %H:%M:%S"),float(total),json.dumps(cart),payment_method,customer,notes))
                    conn.commit()
                    sale_id = c.lastrowid
                    invoice_file = generate_invoice_pdf(sale_id, cart, total, discount_amt, customer, payment_method, notes)
                    st.success(f"Sale completed! Invoice saved: {invoice_file}")
                    with open(invoice_file,"rb") as f:
                        st.download_button(tr("Download Invoice PDF"), f.read(), f"invoice_{sale_id}.pdf","application/pdf")
                    invoice_html = f"<html><body><h2>Invoice #{sale_id}</h2></body></html>"
                    st.download_button(tr("Download Invoice HTML"), invoice_html, f"invoice_{sale_id}.html","text/html")
                    csv_bytes = pd.DataFrame(cart).to_csv(index=False).encode('utf-8')
                    st.download_button(tr("Download Items CSV"), csv_bytes, f"invoice_{sale_id}_items.csv","text/csv")
                    st.session_state.cart=[]

elif page.startswith("📑"):
    st.title("📘 " + tr("Sales Report"))

    # Fetch data
    sales_df = fetch_sales()
    products_df = fetch_products()

    # ----- Date Filter -----
    if not sales_df.empty:
        sales_df['date_parsed'] = pd.to_datetime(sales_df['date'], errors='coerce')
        d1 = st.date_input("From", sales_df['date_parsed'].min().date())
        d2 = st.date_input("To", sales_df['date_parsed'].max().date())
        mask = (sales_df['date_parsed'].dt.date >= d1) & (sales_df['date_parsed'].dt.date <= d2)
        filtered = sales_df[mask].copy()

        if "filtered_sales" not in st.session_state:
            st.session_state.filtered_sales = filtered.copy()

        updated_sales = st.session_state.filtered_sales.copy()
        deleted = False

        # ----- Display Sales with Delete -----
        for i, row in updated_sales.iterrows():
            sale_id = row['sale_id']
            with st.expander(f"{i+1}. 📅 {row.get('date','')} | 👤 {row.get('customer','')} | 💰 {format_currency(row.get('total_amount',0))}"):
                st.write("**Customer:**", row.get('customer',''))
                st.write("**Total Amount:**", format_currency(row.get('total_amount',0)))
                st.write("**Payment Method:**", row.get('payment_method',''))

                # Delete Button
                if st.button("❌ Delete", key=f"delete_sale_report_{sale_id}"):
                    try:
                        c.execute("DELETE FROM sales WHERE sale_id=?", (sale_id,))
                        conn.commit()
                        st.success(f"Sale ID {sale_id} deleted!")

                        # Update session_state
                        st.session_state.filtered_sales = st.session_state.filtered_sales[
                        st.session_state.filtered_sales['sale_id'] != sale_id
                        ]
                        deleted = True

                    except Exception as e:
                        st.error(f"Error deleting sale: {e}")

        # Refresh UI safely
        if deleted:
            st.stop()

        # Display summary table
        st.dataframe(st.session_state.filtered_sales[['sale_id','date','total_amount','payment_method','customer']])
        st.write(tr("Total Sales")+":", format_currency(st.session_state.filtered_sales['total_amount'].sum()))

    else:
        st.info(tr("No Sales"))

    # ----- Low Stock Section -----
    threshold = st.number_input(tr("Low Stock Threshold"), 5.0)
    low_stock = products_df[products_df['stock'] <= threshold] if not products_df.empty else products_df

    if not low_stock.empty:
        if "low_stock_products" not in st.session_state:
            st.session_state.low_stock_products = low_stock.copy()

        updated_low_stock = st.session_state.low_stock_products.copy()
        deleted = False

        # Display low stock products with Delete button
        for i, row in updated_low_stock.iterrows():
            product_id = row['id']  # Assuming 'id' is primary key
            with st.expander(f"{i+1}. {row.get('name','')} | Stock: {row.get('stock',0)} | Category: {row.get('category','')}"):
                st.write("**Barcode:**", row.get('barcode',''))
                st.write("**Cost Price:**", row.get('cost_price',0.0))
                st.write("**Sale Price:**", row.get('sale_price',0.0))

                # Delete Button
                if st.button("❌ Delete", key=f"delete_low_stock_{product_id}"):
                    try:
                        c.execute("DELETE FROM products WHERE id=?", (product_id,))
                        conn.commit()
                        st.success(f"Product '{row.get('name','')}' deleted!")

                        # Update session_state
                        st.session_state.low_stock_products = st.session_state.low_stock_products[
                        st.session_state.low_stock_products['id'] != product_id
                        ]
                        deleted = True

                    except Exception as e:
                        st.error(f"Error deleting product: {e}")

        # Refresh UI safely
        if deleted:
            st.stop()

        # Display final low stock table
        st.dataframe(st.session_state.low_stock_products)

    else:
        st.info(tr("No Low Stock Products"))


elif page.startswith("📈"):
    st.title("📊 " + tr("Visualizations"))

    sales_df = fetch_sales()

    if sales_df.empty:
        st.info(tr("No sales data to visualize."))
        st.stop()

    # -------------------- DATE FIX --------------------
    sales_df["date_parsed"] = pd.to_datetime(sales_df["date"], errors="coerce")

    col1, col2 = st.columns(2)
    with col1:
        d1 = st.date_input(tr("From"), sales_df["date_parsed"].min().date())
    with col2:
        d2 = st.date_input(tr("To"), sales_df["date_parsed"].max().date())

    mask = (sales_df["date_parsed"].dt.date >= d1) & (sales_df["date_parsed"].dt.date <= d2)
    filtered_sales = sales_df[mask]

    # -------------------- PARSE ITEMS JSON --------------------
    all_items = []
    for raw_json in filtered_sales["items_json"]:
        try:
            fixed = raw_json.replace("'", '"')
            items = json.loads(fixed)
            all_items.extend(items)
        except:
            pass

    items_df = pd.DataFrame(all_items)

    # -------------------- GUARD --------------------
    if items_df.empty:
        st.warning(tr("No product data found."))
        st.stop()

    # ---------------------------------------------------------
    #  CHART SELECTOR
    # ---------------------------------------------------------
    chart_options = [
    "📈 Sales Over Time (Line Chart)",
    "📊 Top Selling Products (Bar Chart)",
    "📊 Horizontal Bar Chart",
    "📍 Scatter Plot",
    "🎻 Violin Plot",
    "🔥 Correlation Heatmap",
    "🥧 Pie Chart",
    "📊 Histogram",
    "📦 Box Plot",
    "🌄 Area Chart",
    "⭕ Donut Chart",
    "🫧 Bubble Chart",
    "🌳 Tree Map"
    ]

    choice = st.selectbox(tr("Select Chart"), chart_options)

    # ---------------------------------------------------------
    # 1️⃣ SALES OVER TIME – LINE CHART
    # ---------------------------------------------------------
    if choice == "📈 Sales Over Time (Line Chart)":
        st.subheader("📈 " + tr("Sales Over Time"))
        sales_over_time = filtered_sales.groupby(filtered_sales['date_parsed'].dt.date)['total_amount'].sum()
        st.line_chart(sales_over_time)

    # ---------------------------------------------------------
    # 2️⃣ TOP SELLING PRODUCTS – VERTICAL BAR
    # ---------------------------------------------------------
    elif choice == "📊 Top Selling Products (Bar Chart)":
        st.subheader("📊 " + tr("Top Selling Products"))
        top_products = items_df.groupby("name")["qty"].sum().sort_values(ascending=False).head(10)
        st.bar_chart(top_products)

    # ---------------------------------------------------------
    # 3️⃣ HORIZONTAL BAR CHART
    # ---------------------------------------------------------
    elif choice == "📊 Horizontal Bar Chart":
        st.subheader("📊 " + tr("Top Products (Horizontal Bar Chart)"))
        top_products = items_df.groupby("name")["qty"].sum().sort_values(ascending=True).head(10)
        fig, ax = plt.subplots()
        top_products.plot(kind="barh", ax=ax)
        st.pyplot(fig)

    # ---------------------------------------------------------
    # 4️⃣ SCATTER PLOT — Quantity vs Price
    # ---------------------------------------------------------
    elif choice == "📍 Scatter Plot":
        st.subheader("📍 " + tr("Scatter Plot (Quantity vs Price)"))
        fig, ax = plt.subplots()
        ax.scatter(items_df["qty"], items_df["price"])
        ax.set_xlabel(tr("Quantity"))
        ax.set_ylabel(tr("Price"))
        st.pyplot(fig)

    # ---------------------------------------------------------
    # 5️⃣ VIOLIN PLOT — Price Distribution
    # ---------------------------------------------------------
    elif choice == "🎻 Violin Plot":
        st.subheader("🎻 " + tr("Violin Plot (Price Distribution)"))
        fig, ax = plt.subplots()
        sns.violinplot(data=items_df, y="price", ax=ax)
        st.pyplot(fig)

    # ---------------------------------------------------------
    # 6️⃣ HEATMAP — Correlation
    # ---------------------------------------------------------
    elif choice == "🔥 Correlation Heatmap":
        st.subheader("🔥 " + tr("Correlation Heatmap"))
        fig, ax = plt.subplots()
        sns.heatmap(items_df.select_dtypes(include=[np.number]).corr(), annot=True, cmap="coolwarm", ax=ax)
        st.pyplot(fig)

    # ---------------------------------------------------------
    # 7️⃣ PIE CHART — Top Products
    # ---------------------------------------------------------
    elif choice == "🥧 Pie Chart":
        st.subheader("🥧 " + tr("Pie Chart of Top Products"))
        top_products = items_df.groupby("name")["qty"].sum().head(5)
        fig, ax = plt.subplots()
        top_products.plot(kind="pie", autopct="%1.1f%%", ax=ax)
        ax.set_ylabel("")
        st.pyplot(fig)

    # ---------------------------------------------------------
    # 8️⃣ HISTOGRAM — Price Distribution
    # ---------------------------------------------------------
    elif choice == "📊 Histogram":
        st.subheader("📊 " + tr("Histogram"))
        fig, ax = plt.subplots()
        sns.histplot(items_df["price"], kde=True, ax=ax)
        st.pyplot(fig)

    # ---------------------------------------------------------
    # 9️⃣ BOX PLOT — Price Outliers
    # ---------------------------------------------------------
    elif choice == "📦 Box Plot":
        st.subheader("📦 " + tr("Box Plot"))
        fig, ax = plt.subplots()
        sns.boxplot(data=items_df, y="price", ax=ax)
        st.pyplot(fig)

    # ---------------------------------------------------------
    # 🔟 AREA CHART
    # ---------------------------------------------------------
    elif choice == "🌄 Area Chart":
        st.subheader("🌄 " + tr("Area Chart"))
        sales_over_time = filtered_sales.groupby(filtered_sales['date_parsed'].dt.date)['total_amount'].sum()
        st.area_chart(sales_over_time)

    # ---------------------------------------------------------
    # DONUT CHART
    # ---------------------------------------------------------
    elif choice == "⭕ Donut Chart":
        st.subheader("⭕ " + tr("Donut Chart"))
        # Top 5 products for clarity
        top_products = items_df.groupby("name")["qty"].sum().sort_values(ascending=False).head(5)

        fig, ax = plt.subplots()
        # Fix: unpack 3 values (wedges, texts, autotexts)
        wedges, texts, autotexts = ax.pie(
            top_products,
            wedgeprops={'width': 0.4},
            startangle=90,
            autopct="%1.1f%%"
        )
        ax.set_aspect('equal')
        st.pyplot(fig)

    # ---------------------------------------------------------
    # 1️⃣2️⃣ BUBBLE CHART
    # ---------------------------------------------------------
    elif choice == "🫧 Bubble Chart":
        st.subheader("🫧 " + tr("Bubble Chart (Qty vs Price with Size = Amount)"))
        fig, ax = plt.subplots()
        size = items_df["qty"] * items_df["price"]
        ax.scatter(items_df["qty"], items_df["price"], s=size/5, alpha=0.5)
        ax.set_xlabel(tr("Quantity"))
        ax.set_ylabel(tr("Price"))
        st.pyplot(fig)

    # ---------------------------------------------------------
    # 1️⃣3️⃣ TREE MAP
    # ---------------------------------------------------------
    elif choice == "🌳 Tree Map":
        st.subheader("🌳 " + tr("Tree Map of Top Products"))
        top = items_df.groupby("name")["qty"].sum().sort_values(ascending=False).head(10)
        fig, ax = plt.subplots()
        squarify.plot(sizes=top.values, label=top.index, alpha=0.8)
        plt.axis('off')
        st.pyplot(fig)


elif page.startswith("🔄"):
    st.title("📥 " + tr("Data Import/Export"))
    products_df = fetch_products()
    sales_df = fetch_sales()
    st.download_button("⬇ products.csv", products_df.to_csv(index=False).encode('utf-8'),"products.csv","text/csv")
    st.download_button("⬇ sales.csv", sales_df.to_csv(index=False).encode('utf-8'),"sales.csv","text/csv")

elif page.startswith("❓"):
    st.title("💬 " + tr("Help"))
    st.markdown(f"""
- 📞 Phone No: `+92 XXXXXXXXXX`
- 💬 WhatsApp: `+92 XXXXXXXXXX`
- 📦 {tr('Stock')}: `Ensure stock before sale`
- 🧑 {tr('Customer Name')}: `Optional`
- 💳 {tr('Payment Method')}: `Cash, Card, Mobile`
- 📝 {tr('Notes')}: `Optional`
- 📊 {tr('Dashboard')}: `Today's sales, products, stock`
- 📦 {tr('Inventory')}: `Add/view products`
- 🧾 {tr('Billing / POS')}: `Cart, discount, complete sale`
- 📑 {tr('Sales Report')}: `Reports, low stock alerts`
- 🔄 {tr('Data Import/Export')}: `Export CSV`
- ❓ {tr('Help')}: `This page`
""")

