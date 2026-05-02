import streamlit as st
import pandas as pd
import datetime
import base64

st.set_page_config(page_title="Teknik Doküman Yönetimi", layout="wide")

USERS = [
    {"name": "Ahmet", "role": "Kalite"},
    {"name": "Fatma", "role": "Kalite"},
    {"name": "Ali", "role": "Mühendis"},
    {"name": "Veli", "role": "Mühendis"},
    {"name": "Ayşe", "role": "Üretim"},
    {"name": "Mehmet", "role": "Tasarım"}
]

def get_user(name):
    return next((u for u in USERS if u['name'] == name), None)

# --- Session State Initializations ---
if 'documents' not in st.session_state:
    st.session_state.documents = [
        {
            "id": 1,
            "docNo": "DOC-2024-001",
            "docName": "Tesis Güvenlik Prosedürü",
            "type": "Prosedür",
            "revision": 2,
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
if 'audit_log' not in st.session_state:
    st.session_state.audit_log = []
if 'access_token_expiry' not in st.session_state:
    st.session_state.access_token_expiry = None

# --- Action Logic ---
def log_action(action, target):
    user_role = st.session_state.get('current_role', 'Bilinmiyor')
    st.session_state.audit_log.append({
        "time": datetime.datetime.now().strftime("%H:%M:%S"),
        "user": user_role,
        "action": action,
        "target": target
    })

def go_to_dashboard():
    st.session_state.current_view = 'dashboard'
    st.session_state.selected_doc_id = None
    st.session_state.access_token_expiry = None

def view_document(doc_id):
    st.session_state.selected_doc_id = doc_id
    st.session_state.current_view = 'detail'
    st.session_state.access_token_expiry = datetime.datetime.now() + datetime.timedelta(minutes=5)
    doc = next((d for d in st.session_state.documents if d['id'] == doc_id), None)
    if doc:
        log_action("Görüntüledi (Signed URL)", doc['docNo'])

def check_overall_status(doc):
    all_approved = all(app['status'] == 'Onaylandı' for app in doc['approvals'])
    any_rejected = any(app['status'] == 'Reddedildi' for app in doc['approvals'])
    
    if any_rejected:
        doc['status'] = "Reddedildi"
    elif all_approved:
        doc['status'] = "Onaylandı"
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
    log_action("Onayladı", f"{doc['docNo']} ({user_name} adına)")

def reject_for_user(doc_id, user_name, feedback):
    doc = next((d for d in st.session_state.documents if d['id'] == doc_id), None)
    if not doc: return
    for app in doc['approvals']:
        if app['name'] == user_name:
            app['status'] = "Reddedildi"
            app['feedback'] = feedback
            break
    check_overall_status(doc)
    log_action("Reddetti", f"{doc['docNo']} ({user_name} adına)")

@st.dialog("Onay Akışını Belirle")
def approval_flow_dialog(doc_data):
    st.markdown("Lütfen bu doküman için onaylayıcıları belirleyin:")
    suggested_names = ["Ahmet", "Ali"]
    if doc_data['type'] == "Teknik Resim":
        suggested_names = ["Fatma", "Veli", "Mehmet"]
        st.info("💡 Akıllı Öneri: 'Teknik Resim' tipi dokümanlar geçmişte genelde Fatma (Kalite), Veli (Mühendis) ve Mehmet (Tasarım) tarafından onaylanmış. Sistem bu kişileri otomatik seçti.")
    else:
        st.info("💡 Akıllı Öneri: Bu tip dokümanlar geçmişte genelde Ahmet (Kalite) ve Ali (Mühendis) tarafından onaylanmış.")
    
    selected_approver_names = st.multiselect(
        "Onaylayacak Kişiler:", 
        [u['name'] for u in USERS], 
        default=suggested_names
    )
    
    selected_roles = [get_user(name)['role'] for name in selected_approver_names]
    has_kalite = "Kalite" in selected_roles
    has_muhendis = "Mühendis" in selected_roles
    
    if not has_kalite or not has_muhendis:
        st.warning("⚠️ DİKKAT: Kalite ve Mühendis rollerinden en az 1'er kişi seçilmelidir.")
    else:
        st.success("✅ Gerekli tüm zorunlu roller (Kalite, Mühendis) seçildi.")
        
    if st.button("Sonlandır ve Yükle", type="primary"):
        if not has_kalite or not has_muhendis:
            st.error("Kurallara aykırı: Kalite ve Mühendis rolünden en az 1 kişi seçmelisiniz!")
        else:
            approvals = []
            for name in selected_approver_names:
                approvals.append({
                    "name": name,
                    "role": get_user(name)['role'],
                    "status": "Bekliyor",
                    "feedback": ""
                })
            doc_data['approvals'] = approvals
            st.session_state.documents.append(doc_data)
            log_action("Revizyon Yükledi", f"{doc_data['docNo']} (v{doc_data['revision']})")
            st.success("Doküman başarıyla yüklendi ve onay akışı başlatıldı!")
            st.rerun()

# --- UI Setup ---
st.sidebar.title("🔐 Güvenlik & RBAC")
current_role = st.sidebar.selectbox(
    "👤 Aktif Rol (Demo Login)", 
    ["Operatör", "Mühendis", "Müdür"], 
    index=1,
    help="Rol bazlı erişim testi. Operatör: Sadece görüntüler. Mühendis: Yükler. Müdür: Onaylar."
)
st.session_state.current_role = current_role

st.sidebar.markdown("---")
with st.sidebar.expander("📜 Sistem Denetim İzleri (Audit Log)", expanded=False):
    if len(st.session_state.audit_log) == 0:
        st.info("Henüz bir işlem kaydedilmedi.")
    else:
        for log in reversed(st.session_state.audit_log[-20:]):
            st.markdown(f"**{log['time']}** | `{log['user']}`")
            st.markdown(f"*{log['action']}* ➔ **{log['target']}**")
            st.markdown("---")


if st.session_state.current_view == 'dashboard':
    st.title("Teknik Doküman Yönetimi")
    st.markdown("Modern ve güvenli doküman kontrol merkezi")

    # Upload Section (RBAC Check)
    if current_role in ["Mühendis", "Müdür"]:
        with st.expander("📁 Yeni Doküman Yükle", expanded=False):
            with st.form("upload_form"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    doc_no = st.text_input("Döküman No", placeholder="Örn: DOC-001")
                with col2:
                    doc_name = st.text_input("Doküman Adı", placeholder="Örn: Mastar Teknik Çizimi")
                with col3:
                    doc_type = st.selectbox("Tip", ["Prosedür", "Talimat", "Kılavuz", "Şartname", "Form", "Teknik Resim", "Operasyon Planı", "Standart"])
                
                st.markdown("---")
                st.markdown("### 🚀 Değişiklik / Revizyon Gerekçesi")
                col_r1, col_r2 = st.columns(2)
                with col_r1:
                    rev_reason = st.text_area("Değişiklik Sebebi", placeholder="Örn: Müşteri şikayeti üzerine toleranslar daraltıldı.")
                with col_r2:
                    affected_op = st.text_area("Etkilenen Operasyon", placeholder="Örn: CNC Freze - Operasyon 20")
                diff_desc = st.text_area("Eski vs Yeni Fark Özeti", placeholder="Örn: Çap 20±0.1 olan ölçü 20±0.05 olarak güncellendi.")
                    
                uploaded_file = st.file_uploader("PDF Seçin", type=['pdf'])
                submitted = st.form_submit_button("İleri: Onay Akışını Belirle")

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
                            
                            existing_docs = [d for d in st.session_state.documents if d['docNo'] == doc_no]
                            new_rev_number = max([d.get('revision', 0) for d in existing_docs]) + 1 if existing_docs else 1
                            
                            doc_data = {
                                "id": int(now.timestamp()),
                                "docNo": doc_no,
                                "docName": doc_name,
                                "type": doc_type,
                                "revision": new_rev_number,
                                "date": date_str,
                                "uploader": f"{current_role} (Demo)",
                                "revReason": rev_reason,
                                "affectedOp": affected_op,
                                "diffDesc": diff_desc,
                                "file": uploaded_file.name,
                                "status": "Beklemede",
                                "fileData": file_data_url
                            }
                            
                            approval_flow_dialog(doc_data)
                    else:
                        st.error("Lütfen tüm alanları doldurun ve bir PDF dosyası seçin.")
    else:
        st.info("🔒 Operatör rolündesiniz. Sisteme doküman yükleme veya onaylama yetkiniz bulunmamaktadır. Yalnızca mevcut dokümanları görüntüleyebilirsiniz.")

    st.subheader("Doküman Listesi")

    f_col1, f_col2, f_col3 = st.columns(3)
    with f_col1:
        type_filter = st.selectbox("Tip Filtresi", ["Tümü", "Prosedür", "Talimat", "Kılavuz", "Şartname", "Form", "Teknik Resim", "Operasyon Planı", "Standart"])
    with f_col2:
        status_filter = st.selectbox("Durum Filtresi", ["Aktif Olanlar", "Beklemede", "Onaylandı", "Reddedildi", "Arşivlendi", "Tümü (Arşiv Dahil)"])
    with f_col3:
        search_filter = st.text_input("Doküman Adı / No Ara...")

    filtered_docs = []
    for d in st.session_state.documents:
        if type_filter != "Tümü" and d['type'] != type_filter: continue
        
        if status_filter == "Aktif Olanlar" and d['status'] == "Arşivlendi": continue
        if status_filter not in ["Aktif Olanlar", "Tümü (Arşiv Dahil)"] and d['status'] != status_filter: continue
        
        if search_filter.lower() not in d['docNo'].lower() and search_filter.lower() not in d['docName'].lower(): continue
        filtered_docs.append(d)
    
    if len(filtered_docs) == 0:
        st.info("Kriterlere uygun doküman bulunamadı.")
    else:
        filtered_docs.sort(key=lambda x: x['id'], reverse=True)
        
        cols = st.columns([1.5, 2, 1, 1, 1.5, 1, 1])
        cols[0].markdown("**Döküman No**")
        cols[1].markdown("**Doküman Adı**")
        cols[2].markdown("**Revizyon**")
        cols[3].markdown("**Tip**")
        cols[4].markdown("**Tarih**")
        cols[5].markdown("**Durum**")
        cols[6].markdown("**İşlem**")
        st.markdown("---")
        
        for d in filtered_docs:
            cols = st.columns([1.5, 2, 1, 1, 1.5, 1, 1])
            cols[0].write(d['docNo'])
            cols[1].write(d['docName'])
            cols[2].write(f"v{d.get('revision', 1)}")
            cols[3].write(d['type'])
            cols[4].write(d['date'])
            
            status_color = "orange" if d['status'] == "Beklemede" else "green" if d['status'] == "Onaylandı" else "red" if d['status'] == "Reddedildi" else "grey"
            cols[5].markdown(f"**:{status_color}[{d['status']}]**")
            
            with cols[6]:
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
        col1.markdown(f"**Tip:** {doc['type']} (v{doc.get('revision', 1)})")
        col2.markdown(f"**Tarih:** {doc['date']}")
        col2.markdown(f"**Yükleyen:** {doc['uploader']}")
        
        status_color = "orange" if doc['status'] == "Beklemede" else "green" if doc['status'] == "Onaylandı" else "red" if doc['status'] == "Reddedildi" else "grey"
        col3.markdown(f"**Genel Durum:** :{status_color}[{doc['status']}]")
        
        if doc.get('revReason') or doc.get('affectedOp') or doc.get('diffDesc'):
            st.markdown("---")
            st.markdown("### 🚀 Değişiklik & Revizyon Raporu")
            r_col1, r_col2, r_col3 = st.columns(3)
            with r_col1:
                st.info(f"**Değişiklik Sebebi:**\n\n{doc.get('revReason', '-')}")
            with r_col2:
                st.warning(f"**Etkilenen Operasyon:**\n\n{doc.get('affectedOp', '-')}")
            with r_col3:
                st.success(f"**Eski vs Yeni Fark:**\n\n{doc.get('diffDesc', '-')}")
        
        st.markdown("---")
        st.markdown("### 📝 Onay Akışı Durumu")
        
        has_pending_actions = False
        for app in doc['approvals']:
            app_color = "orange" if app['status'] == "Bekliyor" else "green" if app['status'] == "Onaylandı" else "red"
            st.markdown(f"- **{app['name']}** ({app['role']}) : :{app_color}[{app['status']}]  " + (f"*(Not: {app['feedback']})*" if app['feedback'] else ""))
            
            if doc['status'] == 'Beklemede' and app['status'] == 'Bekliyor':
                has_pending_actions = True
                if current_role == "Müdür":
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
                                
        if has_pending_actions and current_role != "Müdür":
            st.warning("🔒 Sadece 'Müdür' rolündeki kullanıcılar onay/ret işlemi gerçekleştirebilir.")
                            
        st.markdown("---")
        
        # Signed URL Simulation
        if doc.get('fileData'):
            now = datetime.datetime.now()
            expiry = st.session_state.access_token_expiry
            if expiry and now < expiry:
                time_left = expiry - now
                mins, secs = divmod(time_left.seconds, 60)
                st.success(f"🔐 Güvenli Geçici Bağlantı (Signed URL) ile korunmaktadır. (Kalan Süre: {mins} dk {secs} sn)")
                st.markdown(f'<iframe src="{doc["fileData"]}" width="100%" height="800px" style="border: none; border-radius: 8px;"></iframe>', unsafe_allow_html=True)
                
                # Add a download simulation button that logs
                if st.button("⬇️ Güvenli İndir (Audit Log'a Kaydedilir)"):
                    log_action("İndirdi", doc['docNo'])
                    st.toast(f"✅ {doc['docNo']} cihazınıza indirildi ve denetim izine kaydedildi.")
            else:
                st.error("🔒 Güvenli erişim bağlantınızın süresi dolmuştur. Lütfen listeye dönüp dokümanı yeniden açarak yeni bir bağlantı (Signed URL) oluşturun.")
                if st.button("🔄 Yeni Bağlantı Oluştur"):
                    view_document(doc['id'])
                    st.rerun()
        else:
            st.warning("Bu demo dosyasının önizlemesi yok. Yeni PDF yükleyerek deneyin.")
