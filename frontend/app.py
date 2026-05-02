import streamlit as st
import pandas as pd
import requests
import os
import json

st.set_page_config(page_title="Teknik Doküman Yönetimi", layout="wide")

API_URL = os.getenv("API_URL", "http://localhost:8000")

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

if 'current_view' not in st.session_state:
    st.session_state.current_view = 'dashboard'
if 'selected_doc_id' not in st.session_state:
    st.session_state.selected_doc_id = None

def go_to_dashboard():
    st.session_state.current_view = 'dashboard'
    st.session_state.selected_doc_id = None

def view_document(doc_id):
    st.session_state.selected_doc_id = doc_id
    st.session_state.current_view = 'detail'
    # API will log viewing via another endpoint, or we just log locally
    try:
        requests.post(f"{API_URL}/audit-logs/", json={
            "user_role": st.session_state.current_role,
            "action": "Görüntüledi (Signed URL)",
            "target": f"Doc ID: {doc_id}"
        })
    except: pass

@st.dialog("Onay Akışını Belirle")
def approval_flow_dialog(doc_no, doc_name, doc_type, rev_reason, affected_op, diff_desc, file_bytes, file_name, content_type):
    st.markdown("Lütfen bu doküman için onaylayıcıları belirleyin:")
    suggested_names = ["Ahmet", "Ali"]
    if doc_type == "Teknik Resim":
        suggested_names = ["Fatma", "Veli", "Mehmet"]
        st.info("Bilgi: 'Teknik Resim' tipi dokümanlar geçmişte genelde Fatma (Kalite), Veli (Mühendis) ve Mehmet (Tasarım) tarafından onaylanmış. Sistem bu kişileri otomatik seçti.")
    else:
        st.info("Bilgi: Bu tip dokümanlar geçmişte genelde Ahmet (Kalite) ve Ali (Mühendis) tarafından onaylanmış.")
    
    selected_approver_names = st.multiselect(
        "Onaylayacak Kişiler:", 
        [u['name'] for u in USERS], 
        default=suggested_names
    )
    
    selected_roles = [get_user(name)['role'] for name in selected_approver_names]
    has_kalite = "Kalite" in selected_roles
    has_muhendis = "Mühendis" in selected_roles
    
    if not has_kalite or not has_muhendis:
        st.warning("DİKKAT: Kalite ve Mühendis rollerinden en az 1'er kişi seçilmelidir.")
    else:
        st.success("Gerekli tüm zorunlu roller (Kalite, Mühendis) seçildi.")
        
    if st.button("Sonlandır ve Yükle", type="primary"):
        if not has_kalite or not has_muhendis:
            st.error("Kurallara aykırı: Kalite ve Mühendis rolünden en az 1 kişi seçmelisiniz!")
        else:
            approvals = []
            for name in selected_approver_names:
                approvals.append({
                    "user_name": name,
                    "user_role": get_user(name)['role']
                })
            
            # Send to API
            data = {
                "doc_no": doc_no,
                "doc_name": doc_name,
                "doc_type": doc_type,
                "rev_reason": rev_reason or "",
                "affected_op": affected_op or "",
                "diff_desc": diff_desc or "",
                "uploader": st.session_state.current_role,
                "approvals": json.dumps(approvals)
            }
            files = {
                "file": (file_name, file_bytes, content_type)
            }
            try:
                res = requests.post(f"{API_URL}/documents/", data=data, files=files)
                if res.status_code == 200:
                    st.success("Doküman başarıyla yüklendi ve onay akışı başlatıldı!")
                    st.rerun()
                else:
                    st.error(f"Yükleme hatası: {res.text}")
            except Exception as e:
                st.error(f"Sunucuya bağlanılamadı: {e}")

# --- UI Setup ---
st.sidebar.title("Güvenlik ve Erişim Kontrolü")
current_role = st.sidebar.selectbox(
    "Aktif Rol (Demo Login)", 
    ["Operatör", "Mühendis", "Müdür"], 
    index=1,
    help="Rol bazlı erişim testi. Operatör: Sadece görüntüler. Mühendis: Yükler. Müdür: Onaylar."
)
st.session_state.current_role = current_role

st.sidebar.markdown("---")
with st.sidebar.expander("Sistem Denetim İzleri (Audit Log)", expanded=False):
    try:
        logs = requests.get(f"{API_URL}/audit-logs/").json()
        if not logs:
            st.info("Henüz bir işlem kaydedilmedi.")
        else:
            for log in logs:
                st.markdown(f"**{log['time'][:10]} {log['time'][11:19]}** | `{log['user_role']}`")
                st.markdown(f"*{log['action']}* ➔ **{log['target']}**")
                st.markdown("---")
    except:
        st.error("API Bağlantı Hatası")

if st.session_state.current_view == 'dashboard':
    st.title("Teknik Doküman Yönetimi")
    st.markdown("Modern ve güvenli doküman kontrol merkezi")

    # Upload Section (RBAC Check)
    if current_role in ["Mühendis", "Müdür"]:
        with st.expander("Yeni Doküman Yükle", expanded=False):
            with st.form("upload_form"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    doc_no = st.text_input("Döküman No", placeholder="Örn: DOC-001")
                with col2:
                    doc_name = st.text_input("Doküman Adı", placeholder="Örn: Mastar Teknik Çizimi")
                with col3:
                    doc_type = st.selectbox("Tip", ["Prosedür", "Talimat", "Kılavuz", "Şartname", "Form", "Teknik Resim", "Operasyon Planı", "Standart"])
                
                upload_type = st.radio("İşlem Tipi", ["İlk Kez Yükleme (Yeni Doküman)", "Mevcut Dokümanı Revize Et"], horizontal=True)
                uploaded_file = st.file_uploader("PDF Seçin", type=['pdf'])
                
                if upload_type == "Mevcut Dokümanı Revize Et":
                    st.markdown("---")
                    st.markdown("### Değişiklik / Revizyon Gerekçesi")
                    col_r1, col_r2 = st.columns(2)
                    with col_r1:
                        rev_reason = st.text_area("Değişiklik Sebebi", placeholder="Örn: Müşteri şikayeti üzerine toleranslar daraltıldı.")
                    with col_r2:
                        affected_op = st.text_area("Etkilenen Operasyon", placeholder="Örn: CNC Freze - Operasyon 20")
                    diff_desc = st.text_area("Eski vs Yeni Fark Özeti", placeholder="Örn: Çap 20±0.1 olan ölçü 20±0.05 olarak güncellendi.")
                else:
                    rev_reason = ""
                    affected_op = ""
                    diff_desc = ""
                    
                submitted = st.form_submit_button("İleri: Onay Akışını Belirle")

                if submitted:
                    if uploaded_file is not None and doc_no and doc_name:
                        try:
                            docs = requests.get(f"{API_URL}/documents/").json()
                            existing_docs = [d for d in docs if d['doc_no'] == doc_no]
                            
                            if upload_type == "İlk Kez Yükleme (Yeni Doküman)" and len(existing_docs) > 0:
                                st.error(f"Hata: {doc_no} numaralı doküman sistemde zaten var. Güncellemek için 'Mevcut Dokümanı Revize Et' seçeneğini işaretleyin.")
                            elif upload_type == "Mevcut Dokümanı Revize Et" and len(existing_docs) == 0:
                                st.error(f"Hata: {doc_no} numaralı doküman sistemde bulunamadı. Lütfen 'İlk Kez Yükleme' seçeneğini kullanın.")
                            else:
                                pending_rev = next((d for d in existing_docs if d['status'] == 'Beklemede'), None)
                                if pending_rev:
                                    st.error(f"Hata: {doc_no} numaralı dokümanın şu anda incelemede olan bir revizyonu var.")
                                else:
                                    file_bytes = uploaded_file.read()
                                    approval_flow_dialog(doc_no, doc_name, doc_type, rev_reason, affected_op, diff_desc, file_bytes, uploaded_file.name, uploaded_file.type)
                        except Exception as e:
                            st.error(f"Bağlantı hatası: {e}")
                    else:
                        st.error("Lütfen tüm alanları doldurun ve bir PDF dosyası seçin.")
    else:
        st.info("Yetki Sınırı: Operatör rolündesiniz. Sisteme doküman yükleme veya onaylama yetkiniz bulunmamaktadır. Yalnızca mevcut dokümanları görüntüleyebilirsiniz.")

    st.subheader("Doküman Listesi")

    f_col1, f_col2, f_col3 = st.columns(3)
    with f_col1:
        type_filter = st.selectbox("Tip Filtresi", ["Tümü", "Prosedür", "Talimat", "Kılavuz", "Şartname", "Form", "Teknik Resim", "Operasyon Planı", "Standart"])
    with f_col2:
        status_filter = st.selectbox("Durum Filtresi", ["Aktif Olanlar", "Beklemede", "Onaylandı", "Reddedildi", "Arşivlendi", "Tümü (Arşiv Dahil)"])
    with f_col3:
        search_filter = st.text_input("Doküman Adı / No Ara...")

    try:
        all_docs = requests.get(f"{API_URL}/documents/").json()
    except:
        all_docs = []
        st.warning("Veritabanı bağlantısı yok. Lütfen Docker container'ların çalıştığından emin olun.")

    filtered_docs = []
    for d in all_docs:
        if type_filter != "Tümü" and d['doc_type'] != type_filter: continue
        if status_filter == "Aktif Olanlar" and d['status'] == "Arşivlendi": continue
        if status_filter not in ["Aktif Olanlar", "Tümü (Arşiv Dahil)"] and d['status'] != status_filter: continue
        if search_filter.lower() not in d['doc_no'].lower() and search_filter.lower() not in d['doc_name'].lower(): continue
        filtered_docs.append(d)
    
    if len(filtered_docs) == 0:
        st.info("Kriterlere uygun doküman bulunamadı.")
    else:
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
            cols[0].write(d['doc_no'])
            cols[1].write(d['doc_name'])
            cols[2].write(f"v{d.get('revision', 1)}")
            cols[3].write(d['doc_type'])
            cols[4].write(d['created_at'][:10])
            
            status_color = "orange" if d['status'] == "Beklemede" else "green" if d['status'] == "Onaylandı" else "red" if d['status'] == "Reddedildi" else "grey"
            cols[5].markdown(f"**:{status_color}[{d['status']}]**")
            
            with cols[6]:
                if st.button("İncele", key=f"view_{d['id']}"):
                    view_document(d['id'])
                    st.rerun()

elif st.session_state.current_view == 'detail':
    try:
        doc = requests.get(f"{API_URL}/documents/{st.session_state.selected_doc_id}").json()
    except:
        doc = None
        st.error("Doküman verisi alınamadı.")

    if doc:
        if st.button("Listeye Dön"):
            go_to_dashboard()
            st.rerun()
            
        st.header(f"Doküman Detayı: {doc['doc_no']}")
        
        col1, col2, col3 = st.columns(3)
        col1.markdown(f"**Doküman Adı:** {doc['doc_name']}")
        col1.markdown(f"**Tip:** {doc['doc_type']} (v{doc.get('revision', 1)})")
        col2.markdown(f"**Tarih:** {doc['created_at'][:10]}")
        col2.markdown(f"**Yükleyen:** {doc['uploader']}")
        
        status_color = "orange" if doc['status'] == "Beklemede" else "green" if doc['status'] == "Onaylandı" else "red" if doc['status'] == "Reddedildi" else "grey"
        col3.markdown(f"**Genel Durum:** :{status_color}[{doc['status']}]")
        
        if doc.get('rev_reason') or doc.get('affected_op') or doc.get('diff_desc'):
            st.markdown("---")
            st.markdown("### Değişiklik ve Revizyon Raporu")
            r_col1, r_col2, r_col3 = st.columns(3)
            with r_col1:
                st.info(f"**Değişiklik Sebebi:**\n\n{doc.get('rev_reason', '-')}")
            with r_col2:
                st.warning(f"**Etkilenen Operasyon:**\n\n{doc.get('affected_op', '-')}")
            with r_col3:
                st.success(f"**Eski vs Yeni Fark:**\n\n{doc.get('diff_desc', '-')}")
        
        st.markdown("---")
        st.markdown("### Onay Akışı Durumu")
        
        has_pending_actions = False
        for app in doc['approvals']:
            app_color = "orange" if app['status'] == "Bekliyor" else "green" if app['status'] == "Onaylandı" else "red"
            st.markdown(f"- **{app['user_name']}** ({app['user_role']}) : :{app_color}[{app['status']}]  " + (f"*(Not: {app['feedback']})*" if app['feedback'] else ""))
            
            if doc['status'] == 'Beklemede' and app['status'] == 'Bekliyor':
                has_pending_actions = True
                if current_role == "Müdür":
                    sub_col1, sub_col2, sub_col3 = st.columns([2, 2, 8])
                    with sub_col1:
                        if st.button(f"Onayla ({app['user_name']})", key=f"app_{doc['id']}_{app['user_name']}"):
                            requests.post(f"{API_URL}/approvals/{app['id']}/approve?user_name={st.session_state.current_role}")
                            st.rerun()
                    with sub_col2:
                        with st.popover(f"Reddet ({app['user_name']})"):
                            reject_reason = st.text_area("Ret Nedeni", key=f"rej_res_{doc['id']}_{app['user_name']}")
                            if st.button("Kaydet", key=f"rej_btn_{doc['id']}_{app['user_name']}"):
                                requests.post(f"{API_URL}/approvals/{app['id']}/reject?user_name={st.session_state.current_role}&feedback={reject_reason}")
                                st.rerun()
                                
        if has_pending_actions and current_role != "Müdür":
            st.warning("Yetki Sınırı: Sadece 'Müdür' rolündeki kullanıcılar onay/ret işlemi gerçekleştirebilir.")
                            
        st.markdown("---")
        
        # Signed URL Simulation / Fetching
        try:
            url_res = requests.get(f"{API_URL}/documents/{doc['id']}/signed-url").json()
            if "url" in url_res and url_res["url"]:
                st.success("Güvenli Geçici Bağlantı (Signed URL) sağlandı.")
                st.markdown(f'<iframe src="{url_res["url"]}" width="100%" height="800px" style="border: none; border-radius: 8px;"></iframe>', unsafe_allow_html=True)
                
                if st.button("Güvenli İndir (Audit Log'a Kaydedilir)"):
                    requests.post(f"{API_URL}/audit-logs/", json={
                        "user_role": st.session_state.current_role,
                        "action": "İndirdi",
                        "target": doc['doc_no']
                    })
                    st.toast(f"{doc['doc_no']} cihazınıza indirildi ve denetim izine kaydedildi.")
            else:
                st.warning("Bu dokümanın PDF dosyası MinIO'da bulunamadı.")
        except:
            st.error("MinIO (S3) bağlantısı sağlanamadı. Dosya görüntülenemiyor.")
