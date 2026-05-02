import streamlit as st
import pandas as pd
import datetime
import base64

USERS = [
    {"name": "Ahmet", "role": "Kalite"},
    {"name": "Fatma", "role": "Kalite"},
    {"name": "Ali", "role": "Mühendis"},
    {"name": "Veli", "role": "Mühendis"},
    {"name": "Ayşe", "role": "Üretim"},
    {"name": "Mehmet", "role": "Tasarım"}
]

# Helper to find a user by name
def get_user(name):
    return next((u for u in USERS if u['name'] == name), None)

# --- State Initialization ---
if 'documents' not in st.session_state:
    st.session_state.documents = [
        {
            "id": 1,
            "docNo": "DOC-2024-001",
            "docName": "Tesis Güvenlik Prosedürü",
            "type": "Prosedür",
            "date": "02 Mayıs 2026",
            "uploader": "Sistem",
            "approvals": [
                {"name": "Ahmet", "role": "Kalite", "status": "Bekliyor", "feedback": ""},
                {"name": "Ali", "role": "Mühendis", "status": "Bekliyor", "feedback": ""}
            ],
            "file": "guvenlik_proseduru_v2.pdf",
            "status": "Beklemede",
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

def check_overall_status(doc):
    all_approved = all(app['status'] == 'Onaylandı' for app in doc['approvals'])
    any_rejected = any(app['status'] == 'Reddedildi' for app in doc['approvals'])
    
    if any_rejected:
        doc['status'] = "Reddedildi"
    elif all_approved:
        doc['status'] = "Onaylandı"
        # Auto-archive older ones
        for d in st.session_state.documents:
            if d['docNo'] == doc['docNo'] and d['id'] != doc['id'] and d['status'] == "Onaylandı":
                d['status'] = "Arşivlendi"

def approve_for_user(doc_id, user_name):
    doc = next((d for d in st.session_state.documents if d['id'] == doc_id), None)
    if not doc: return
    
    for app in doc['approvals']:
        if app['name'] == user_name:
            app['status'] = "Onaylandı"
            app['feedback'] = "Uygun"
            break
            
    check_overall_status(doc)

def reject_for_user(doc_id, user_name, feedback):
    doc = next((d for d in st.session_state.documents if d['id'] == doc_id), None)
    if not doc: return
    
    for app in doc['approvals']:
        if app['name'] == user_name:
            app['status'] = "Reddedildi"
            app['feedback'] = feedback
            break
            
    check_overall_status(doc)

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
            
            st.markdown("---")
            st.markdown("### 👥 Onay Akışı Belirleme")
            
            # Smart Suggestion logic
            suggested_names = ["Ahmet", "Ali"]
            if doc_type == "Teknik Resim":
                suggested_names = ["Fatma", "Veli", "Mehmet"]
                st.info("💡 Akıllı Öneri: 'Teknik Resim' tipi dokümanlar geçmişte genelde Fatma (Kalite), Veli (Mühendis) ve Mehmet (Tasarım) tarafından onaylanmış. Sistem bu kişileri otomatik seçti.")
            else:
                st.info("💡 Akıllı Öneri: Bu tip dokümanlar geçmişte genelde Ahmet (Kalite) ve Ali (Mühendis) tarafından onaylanmış.")
            
            selected_approver_names = st.multiselect(
                "Onaylayacak Kişiler (Sistem önerisi eklendi, istediğiniz gibi değiştirebilirsiniz):", 
                [u['name'] for u in USERS], 
                default=suggested_names
            )
            
            # Validate roles
            selected_roles = [get_user(name)['role'] for name in selected_approver_names]
            has_kalite = "Kalite" in selected_roles
            has_muhendis = "Mühendis" in selected_roles
            
            if not has_kalite or not has_muhendis:
                st.warning("⚠️ DİKKAT: Kalite ve Mühendis rollerinden en az 1'er kişi seçilmelidir. Lütfen bu rolleri boş bırakmayın.")
            else:
                st.success("✅ Gerekli tüm zorunlu roller (Kalite, Mühendis) seçildi.")
                
            uploaded_file = st.file_uploader("PDF Seçin", type=['pdf'])
            submitted = st.form_submit_button("Yükle ve Onaya Gönder")

            if submitted:
                if not has_kalite or not has_muhendis:
                    st.error("Kurallara aykırı: Kalite ve Mühendis rolünden en az 1 kişi seçmelisiniz!")
                elif uploaded_file is not None and doc_no and doc_name:
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
                        
                        approvals = []
                        for name in selected_approver_names:
                            approvals.append({
                                "name": name,
                                "role": get_user(name)['role'],
                                "status": "Bekliyor",
                                "feedback": ""
                            })
                            
                        new_doc = {
                            "id": int(now.timestamp()),
                            "docNo": doc_no,
                            "docName": doc_name,
                            "type": doc_type,
                            "date": date_str,
                            "uploader": "Mevcut Kullanıcı",
                            "approvals": approvals,
                            "file": uploaded_file.name,
                            "status": "Beklemede",
                            "fileData": file_data_url
                        }
                        st.session_state.documents.append(new_doc)
                        st.success("Doküman başarıyla yüklendi ve onay akışı başlatıldı!")
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
        filtered_docs.sort(key=lambda x: x['id'], reverse=True)
        
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
        if st.button("⬅ Listeye Dön"):
            go_to_dashboard()
            st.rerun()
            
        st.header(f"Doküman Detayı: {doc['docNo']}")
        
        col1, col2, col3 = st.columns(3)
        col1.markdown(f"**Doküman Adı:** {doc['docName']}")
        col1.markdown(f"**Tip:** {doc['type']}")
        col2.markdown(f"**Tarih:** {doc['date']}")
        col2.markdown(f"**Yükleyen:** {doc['uploader']}")
        
        status_color = "orange" if doc['status'] == "Beklemede" else "green" if doc['status'] == "Onaylandı" else "red" if doc['status'] == "Reddedildi" else "grey"
        col3.markdown(f"**Genel Durum:** :{status_color}[{doc['status']}]")
        
        st.markdown("### 📝 Onay Akışı Durumu")
        
        for app in doc['approvals']:
            app_color = "orange" if app['status'] == "Bekliyor" else "green" if app['status'] == "Onaylandı" else "red"
            st.markdown(f"- **{app['name']}** ({app['role']}) : :{app_color}[{app['status']}]  " + (f"*(Not: {app['feedback']})*" if app['feedback'] else ""))
            
            # If doc is pending and this user is waiting, show buttons to simulate them
            if doc['status'] == 'Beklemede' and app['status'] == 'Bekliyor':
                sub_col1, sub_col2, sub_col3 = st.columns([2, 2, 8])
                with sub_col1:
                    if st.button(f"✅ Onayla ({app['name']})", key=f"app_{doc['id']}_{app['name']}"):
                        approve_for_user(doc['id'], app['name'])
                        st.rerun()
                with sub_col2:
                    with st.popover(f"❌ Reddet ({app['name']})"):
                        reject_reason = st.text_area("Ret Nedeni", key=f"rej_res_{doc['id']}_{app['name']}")
                        if st.button("Kaydet", key=f"rej_btn_{doc['id']}_{app['name']}"):
                            reject_for_user(doc['id'], app['name'], reject_reason)
                            st.rerun()
                            
        st.markdown("---")
        if doc.get('fileData'):
            st.markdown(f'<iframe src="{doc["fileData"]}" width="100%" height="800px" style="border: none; border-radius: 8px;"></iframe>', unsafe_allow_html=True)
        else:
            st.warning("Bu demo dosyasının önizlemesi yok. Yeni PDF yükleyerek deneyin.")
