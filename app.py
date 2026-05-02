import streamlit as st
import pandas as pd
import datetime
import base64

# --- State Initialization ---
if 'documents' not in st.session_state:
    st.session_state.documents = [
        {
            "id": 1,
            "docNo": "DOC-2024-001",
            "docName": "Tesis Güvenlik Prosedürü",
            "type": "Prosedür",
            "date": "02 Mayıs 2026",
            "uploader": "Ahmet Yılmaz",
            "approver": "-",
            "file": "guvenlik_proseduru_v2.pdf",
            "status": "Beklemede",
            "feedback": "",
            "fileData": None
        },
        {
            "id": 2,
            "docNo": "DOC-2024-002",
            "docName": "Pres Makinesi Kullanım Talimatı",
            "type": "Talimat",
            "date": "15 Nisan 2026",
            "uploader": "Mehmet Kaya",
            "approver": "Ayşe Demir",
            "file": "makine_kullanim_talimati.pdf",
            "status": "Onaylandı",
            "feedback": "Uygundur.",
            "fileData": None
        }
    ]

if 'current_view' not in st.session_state:
    st.session_state.current_view = 'dashboard'

if 'selected_doc_id' not in st.session_state:
    st.session_state.selected_doc_id = None

# --- Helper Functions ---
def go_to_dashboard():
    st.session_state.current_view = 'dashboard'
    st.session_state.selected_doc_id = None

def view_document(doc_id):
    st.session_state.selected_doc_id = doc_id
    st.session_state.current_view = 'detail'

def approve_doc(doc_id):
    target_doc = next((d for d in st.session_state.documents if d['id'] == doc_id), None)
    if not target_doc: return
    
    for d in st.session_state.documents:
        if d['docNo'] == target_doc['docNo'] and d['id'] != doc_id and d['status'] == "Onaylandı":
            d['status'] = "Arşivlendi"
            
    target_doc['status'] = "Onaylandı"
    target_doc['feedback'] = "Onaylandı"
    target_doc['approver'] = "Yönetici"

def reject_doc(doc_id, feedback):
    for d in st.session_state.documents:
        if d['id'] == doc_id:
            d['status'] = "Reddedildi"
            d['feedback'] = feedback
            d['approver'] = "Yönetici"

# --- UI Setup ---
st.set_page_config(page_title="Teknik Doküman Yönetimi", layout="wide")

if st.session_state.current_view == 'dashboard':
    st.title("Teknik Doküman Yönetimi")
    st.markdown("Modern ve güvenli doküman kontrol merkezi")

    # Upload Section
    with st.expander("📁 Yeni Doküman Yükle", expanded=True):
        with st.form("upload_form"):
            col1, col2, col3 = st.columns(3)
            with col1:
                doc_no = st.text_input("Döküman No", placeholder="Örn: DOC-001")
            with col2:
                doc_name = st.text_input("Doküman Adı", placeholder="Örn: Mastar Teknik Çizimi")
            with col3:
                doc_type = st.selectbox("Tip", ["Prosedür", "Talimat", "Kılavuz", "Şartname", "Form", "Teknik Resim", "Operasyon Planı", "Standart"])
            
            uploaded_file = st.file_uploader("PDF Seçin", type=['pdf'])
            submitted = st.form_submit_button("Yükle")

            if submitted:
                if uploaded_file is not None and doc_no and doc_name:
                    pending_rev = next((d for d in st.session_state.documents if d['docNo'] == doc_no and d['status'] == 'Beklemede'), None)
                    if pending_rev:
                        st.error(f"Hata: {doc_no} numaralı dokümanın şu anda incelemede olan bir revizyonu var. Aynı anda birden fazla revizyon onaya sunulamaz.")
                    else:
                        file_bytes = uploaded_file.read()
                        encoded = base64.b64encode(file_bytes).decode('utf-8')
                        file_data_url = f"data:application/pdf;base64,{encoded}"
                        
                        months = ["", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
                        now = datetime.datetime.now()
                        date_str = f"{now.day} {months[now.month]} {now.year}"
                        
                        new_doc = {
                            "id": int(now.timestamp()),
                            "docNo": doc_no,
                            "docName": doc_name,
                            "type": doc_type,
                            "date": date_str,
                            "uploader": "Mevcut Kullanıcı",
                            "approver": "-",
                            "file": uploaded_file.name,
                            "status": "Beklemede",
                            "feedback": "",
                            "fileData": file_data_url
                        }
                        st.session_state.documents.append(new_doc)
                        st.success("Doküman başarıyla yüklendi!")
                        st.rerun()
                else:
                    st.error("Lütfen tüm alanları doldurun ve bir PDF dosyası seçin.")

    st.subheader("Doküman Listesi")

    # Filters
    f_col1, f_col2, f_col3 = st.columns(3)
    with f_col1:
        type_filter = st.selectbox("Tip Filtresi", ["Tümü", "Prosedür", "Talimat", "Kılavuz", "Şartname", "Form", "Teknik Resim", "Operasyon Planı", "Standart"])
    with f_col2:
        status_filter = st.selectbox("Durum Filtresi", ["Tümü", "Beklemede", "Onaylandı", "Reddedildi", "Arşivlendi"])
    with f_col3:
        search_filter = st.text_input("Doküman Adı / No Ara...")

    # Filter data
    filtered_docs = []
    for d in st.session_state.documents:
        if type_filter != "Tümü" and d['type'] != type_filter: continue
        if status_filter != "Tümü" and d['status'] != status_filter: continue
        if search_filter.lower() not in d['docNo'].lower() and search_filter.lower() not in d['docName'].lower(): continue
        filtered_docs.append(d)
    
    if len(filtered_docs) == 0:
        st.info("Kriterlere uygun doküman bulunamadı.")
    else:
        # Sort descending by ID
        filtered_docs.sort(key=lambda x: x['id'], reverse=True)
        
        # Header
        cols = st.columns([1.5, 2, 1, 1.5, 1, 1])
        cols[0].markdown("**Döküman No**")
        cols[1].markdown("**Doküman Adı**")
        cols[2].markdown("**Tip**")
        cols[3].markdown("**Tarih**")
        cols[4].markdown("**Durum**")
        cols[5].markdown("**İşlem**")
        st.markdown("---")
        
        for d in filtered_docs:
            cols = st.columns([1.5, 2, 1, 1.5, 1, 1])
            cols[0].write(d['docNo'])
            cols[1].write(d['docName'])
            cols[2].write(d['type'])
            cols[3].write(d['date'])
            
            status_color = "orange" if d['status'] == "Beklemede" else "green" if d['status'] == "Onaylandı" else "red" if d['status'] == "Reddedildi" else "grey"
            cols[4].markdown(f"**:{status_color}[{d['status']}]**")
            
            with cols[5]:
                if st.button("İncele", key=f"view_{d['id']}"):
                    view_document(d['id'])
                    st.rerun()

elif st.session_state.current_view == 'detail':
    doc = next((d for d in st.session_state.documents if d['id'] == st.session_state.selected_doc_id), None)
    if doc:
        if st.button("⬅ Geri Dön"):
            go_to_dashboard()
            st.rerun()
            
        st.header(f"Doküman Detayı: {doc['docNo']}")
        
        col1, col2, col3 = st.columns(3)
        col1.markdown(f"**Doküman Adı:** {doc['docName']}")
        col1.markdown(f"**Tip:** {doc['type']}")
        col2.markdown(f"**Tarih:** {doc['date']}")
        col2.markdown(f"**Yükleyen:** {doc['uploader']}")
        col3.markdown(f"**Onaylayan:** {doc['approver']}")
        
        status_color = "orange" if doc['status'] == "Beklemede" else "green" if doc['status'] == "Onaylandı" else "red" if doc['status'] == "Reddedildi" else "grey"
        col3.markdown(f"**Durum:** :{status_color}[{doc['status']}]")
        
        if doc['feedback']:
            st.error(f"**Geri Bildirim:** {doc['feedback']}")
            
        if doc['status'] == 'Beklemede':
            st.markdown("---")
            col_a, col_b = st.columns([1, 1])
            with col_a:
                if st.button("✅ Onayla", type="primary", use_container_width=True):
                    approve_doc(doc['id'])
                    st.rerun()
            with col_b:
                with st.popover("❌ Reddet", use_container_width=True):
                    reject_reason = st.text_area("Ret Nedeni")
                    if st.button("Reddet ve Kaydet"):
                        reject_doc(doc['id'], reject_reason)
                        st.rerun()
        
        st.markdown("---")
        if doc.get('fileData'):
            st.markdown(f'<iframe src="{doc["fileData"]}" width="100%" height="800px" style="border: none; border-radius: 8px;"></iframe>', unsafe_allow_html=True)
        else:
            st.warning("Bu demo dosyasının önizlemesi yok. Yeni PDF yükleyerek deneyin.")
