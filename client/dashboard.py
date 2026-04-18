"""
Digital Asset Protection -- Dashboard & Integration
Person C (Harsha) -- Streamlit Web UI

Tabs: Asset Registry | Custody Trail | Leak Map
Sidebar: PDF Export, System Status, Image Verification
"""

import streamlit as st
import pandas as pd
import json
import os
import tempfile
from datetime import datetime

import api
import bait_api
from evidence_report import generate_report
from db_schema import init_db

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Digital Asset Protection",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS -- premium dark theme, no emojis
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    /* ---- Import font ---- */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* ---- Global ---- */
    .stApp {
        font-family: 'Inter', sans-serif;
    }

    /* ---- Main header ---- */
    .main-header {
        background: linear-gradient(135deg, #0f3460 0%, #16213e 50%, #1a1a2e 100%);
        padding: 28px 36px;
        border-radius: 16px;
        margin-bottom: 28px;
        border: 1px solid rgba(255,255,255,0.06);
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
    }
    .main-header h1 {
        color: #e0e0e0;
        font-size: 28px;
        font-weight: 800;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .main-header p {
        color: #8892b0;
        font-size: 14px;
        margin: 6px 0 0 0;
        font-weight: 400;
    }

    /* ---- Metric cards ---- */
    .metric-row {
        display: flex;
        gap: 16px;
        margin-bottom: 24px;
    }
    .metric-card {
        background: linear-gradient(135deg, #16213e, #1a1a2e);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 12px;
        padding: 20px 24px;
        flex: 1;
        box-shadow: 0 4px 16px rgba(0,0,0,0.2);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 24px rgba(0,0,0,0.3);
    }
    .metric-card .label {
        color: #8892b0;
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 6px;
    }
    .metric-card .value {
        color: #e0e0e0;
        font-size: 28px;
        font-weight: 700;
    }
    .metric-card .value.green { color: #00d68f; }
    .metric-card .value.red { color: #ff6b6b; }
    .metric-card .value.blue { color: #6cb4ee; }
    .metric-card .value.orange { color: #ffa94d; }

    /* ---- Status badges ---- */
    .badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 6px;
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 0.5px;
        text-transform: uppercase;
    }
    .badge-verified {
        background: rgba(0, 214, 143, 0.15);
        color: #00d68f;
        border: 1px solid rgba(0, 214, 143, 0.3);
    }
    .badge-violated {
        background: rgba(255, 107, 107, 0.15);
        color: #ff6b6b;
        border: 1px solid rgba(255, 107, 107, 0.3);
    }
    .badge-licensed {
        background: rgba(0, 214, 143, 0.15);
        color: #00d68f;
        border: 1px solid rgba(0, 214, 143, 0.3);
    }
    .badge-distributed {
        background: rgba(108, 180, 238, 0.15);
        color: #6cb4ee;
        border: 1px solid rgba(108, 180, 238, 0.3);
    }
    .badge-detected {
        background: rgba(255, 169, 77, 0.15);
        color: #ffa94d;
        border: 1px solid rgba(255, 169, 77, 0.3);
    }
    .badge-pending {
        background: rgba(136, 146, 176, 0.15);
        color: #8892b0;
        border: 1px solid rgba(136, 146, 176, 0.3);
    }

    /* ---- Data section ---- */
    .section-header {
        color: #e0e0e0;
        font-size: 18px;
        font-weight: 700;
        margin: 20px 0 12px 0;
        padding-bottom: 8px;
        border-bottom: 2px solid rgba(255,255,255,0.08);
    }

    /* ---- Detail card ---- */
    .detail-card {
        background: linear-gradient(135deg, #16213e, #1a1a2e);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 12px;
        padding: 20px 24px;
        margin-bottom: 16px;
        box-shadow: 0 4px 16px rgba(0,0,0,0.2);
    }
    .detail-card .field-label {
        color: #8892b0;
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        margin-bottom: 2px;
    }
    .detail-card .field-value {
        color: #e0e0e0;
        font-size: 14px;
        font-weight: 500;
        margin-bottom: 12px;
        word-break: break-all;
    }
    .detail-card .field-value.mono {
        font-family: 'Courier New', monospace;
        font-size: 12px;
        background: rgba(0,0,0,0.2);
        padding: 6px 10px;
        border-radius: 6px;
        border: 1px solid rgba(255,255,255,0.05);
    }

    /* ---- Timeline ---- */
    .timeline-item {
        position: relative;
        padding: 16px 20px 16px 36px;
        margin-left: 12px;
        border-left: 2px solid rgba(255,255,255,0.1);
        margin-bottom: 4px;
    }
    .timeline-item::before {
        content: '';
        position: absolute;
        left: -6px;
        top: 20px;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background: #6cb4ee;
        border: 2px solid #16213e;
    }
    .timeline-item.violated::before { background: #ff6b6b; }
    .timeline-item.licensed::before { background: #00d68f; }
    .timeline-item.distributed::before { background: #6cb4ee; }
    .timeline-item .t-time {
        color: #8892b0;
        font-size: 12px;
        font-weight: 500;
    }
    .timeline-item .t-event {
        color: #e0e0e0;
        font-size: 14px;
        font-weight: 600;
        margin: 4px 0;
    }
    .timeline-item .t-detail {
        color: #a0a8c0;
        font-size: 12px;
    }

    /* ---- Propagation chain ---- */
    .prop-chain {
        display: flex;
        align-items: center;
        gap: 8px;
        flex-wrap: wrap;
        margin: 12px 0;
    }
    .prop-node {
        background: linear-gradient(135deg, #16213e, #1a1a2e);
        border: 1px solid rgba(255, 169, 77, 0.3);
        border-radius: 8px;
        padding: 10px 14px;
        text-align: center;
        min-width: 150px;
    }
    .prop-node .node-channel {
        color: #ffa94d;
        font-size: 12px;
        font-weight: 600;
    }
    .prop-node .node-time {
        color: #8892b0;
        font-size: 10px;
        margin-top: 2px;
    }
    .prop-node .node-type {
        font-size: 9px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-top: 4px;
    }
    .prop-arrow {
        color: #8892b0;
        font-size: 18px;
        font-weight: 700;
    }

    /* ---- Match result ---- */
    .match-result {
        background: linear-gradient(135deg, rgba(0,214,143,0.05), rgba(0,214,143,0.02));
        border: 1px solid rgba(0,214,143,0.2);
        border-radius: 12px;
        padding: 20px 24px;
        margin: 16px 0;
    }
    .match-result.no-match {
        background: linear-gradient(135deg, rgba(255,107,107,0.05), rgba(255,107,107,0.02));
        border: 1px solid rgba(255,107,107,0.2);
    }

    /* ---- Sidebar styling ---- */
    .sidebar-section {
        background: linear-gradient(135deg, #16213e, #1a1a2e);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 16px;
    }
    .sidebar-title {
        color: #e0e0e0;
        font-size: 13px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 12px;
    }

    /* ---- Hide streamlit defaults ---- */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}

    /* ---- Tab styling ---- */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 24px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Initialize DB
# ---------------------------------------------------------------------------
init_db()


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown("""
<div class="main-header">
    <h1>DIGITAL ASSET PROTECTION</h1>
    <p>Media DNA Fingerprinting | Chain of Custody | Honeypot Leak Detection</p>
</div>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
@st.cache_data(ttl=5)
def load_assets():
    return api.get_asset_list()

@st.cache_data(ttl=5)
def load_custody(asset_id):
    return api.get_custody_trail(asset_id)

@st.cache_data(ttl=5)
def load_baits():
    return bait_api.get_bait_list()

@st.cache_data(ttl=5)
def load_leak_trail(bait_id):
    return bait_api.get_leak_trail(bait_id)


assets = load_assets()
baits = load_baits()


# ---------------------------------------------------------------------------
# Summary metrics
# ---------------------------------------------------------------------------
total_assets = len(assets)
all_events = []
for a in assets:
    all_events.extend(load_custody(a["asset_id"]))
total_events = len(all_events)
violations = sum(1 for e in all_events if e["event_type"] == "violated")
detected_baits = sum(1 for b in baits if b.get("detected_at"))

st.markdown(f"""
<div class="metric-row">
    <div class="metric-card">
        <div class="label">Registered Assets</div>
        <div class="value blue">{total_assets}</div>
    </div>
    <div class="metric-card">
        <div class="label">Custody Events</div>
        <div class="value green">{total_events}</div>
    </div>
    <div class="metric-card">
        <div class="label">Violations Detected</div>
        <div class="value red">{violations}</div>
    </div>
    <div class="metric-card">
        <div class="label">Baits Triggered</div>
        <div class="value orange">{detected_baits} / {len(baits)}</div>
    </div>
</div>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("""
    <div class="sidebar-title">SYSTEM CONTROLS</div>
    """, unsafe_allow_html=True)

    # PDF Export
    st.markdown("---")
    st.markdown("**Evidence Report Export**")
    if assets:
        asset_options = {f"{a['asset_id']} -- {a['name']}": a["asset_id"] for a in assets}
        selected_export = st.selectbox(
            "Select asset for report",
            options=list(asset_options.keys()),
            key="export_select"
        )
        export_asset_id = asset_options[selected_export]

        if st.button("Generate PDF Report", key="btn_export", use_container_width=True):
            with st.spinner("Generating evidence report..."):
                try:
                    pdf_path = generate_report(export_asset_id)
                    with open(pdf_path, "rb") as f:
                        pdf_bytes = f.read()
                    st.download_button(
                        label="Download Report",
                        data=pdf_bytes,
                        file_name=os.path.basename(pdf_path),
                        mime="application/pdf",
                        use_container_width=True,
                    )
                    st.success(f"Report ready: {os.path.basename(pdf_path)}")
                except Exception as e:
                    st.error(f"Report generation failed: {e}")

    # System status
    st.markdown("---")
    st.markdown("**System Status**")
    db_exists = os.path.exists(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets.db")
    )
    st.markdown(f"Database: {'Connected' if db_exists else 'Not Found'}")
    st.markdown(f"Assets loaded: {total_assets}")
    st.markdown(f"Baits tracked: {len(baits)}")
    st.markdown(f"Last refresh: {datetime.now().strftime('%H:%M:%S')}")

    # Image verification in sidebar
    st.markdown("---")
    st.markdown("**Image Verification**")
    uploaded_file = st.file_uploader(
        "Upload a suspected copy",
        type=["jpg", "jpeg", "png", "bmp", "webp"],
        key="verify_upload"
    )


# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["ASSET REGISTRY", "CUSTODY TRAIL", "LEAK MAP"])


# ===========================================================================
# TAB 1: Asset Registry
# ===========================================================================
with tab1:
    st.markdown('<div class="section-header">Registered Assets</div>', unsafe_allow_html=True)

    if not assets:
        st.info("No assets registered yet. Waiting for Person A's module.")
    else:
        # Asset table
        df = pd.DataFrame(assets)
        display_cols = ["asset_id", "name", "owner_org", "phash", "registered_at"]
        available_cols = [c for c in display_cols if c in df.columns]
        st.dataframe(
            df[available_cols],
            use_container_width=True,
            hide_index=True,
            column_config={
                "asset_id": st.column_config.TextColumn("Asset ID", width="small"),
                "name": st.column_config.TextColumn("Asset Name", width="medium"),
                "owner_org": st.column_config.TextColumn("Owner", width="medium"),
                "phash": st.column_config.TextColumn("pHash", width="small"),
                "registered_at": st.column_config.TextColumn("Registered", width="small"),
            }
        )

        # Asset detail view
        st.markdown('<div class="section-header">Asset Detail</div>', unsafe_allow_html=True)
        asset_options_detail = {f"{a['asset_id']} -- {a['name']}": a for a in assets}
        selected_detail = st.selectbox(
            "Select an asset to inspect",
            options=list(asset_options_detail.keys()),
            key="asset_detail_select"
        )
        selected_asset = asset_options_detail[selected_detail]

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            <div class="detail-card">
                <div class="field-label">Asset ID</div>
                <div class="field-value">{selected_asset['asset_id']}</div>
                <div class="field-label">Name</div>
                <div class="field-value">{selected_asset['name']}</div>
                <div class="field-label">Owner Organization</div>
                <div class="field-value">{selected_asset['owner_org']}</div>
                <div class="field-label">Registered At</div>
                <div class="field-value">{selected_asset['registered_at']}</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div class="detail-card">
                <div class="field-label">Perceptual Hash (pHash)</div>
                <div class="field-value mono">{selected_asset.get('phash', 'N/A')}</div>
                <div class="field-label">Histogram Signature</div>
                <div class="field-value mono">{selected_asset.get('histogram_sig', 'N/A')}</div>
                <div class="field-label">Metadata SHA-256</div>
                <div class="field-value mono">{selected_asset.get('metadata_sha', 'N/A')}</div>
                <div class="field-label">Combined DNA</div>
                <div class="field-value mono">{selected_asset.get('dna_combined', 'N/A')}</div>
            </div>
            """, unsafe_allow_html=True)

    # Image verification result display
    if uploaded_file is not None:
        st.markdown('<div class="section-header">Verification Result</div>', unsafe_allow_html=True)

        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            tmp.write(uploaded_file.getbuffer())
            tmp_path = tmp.name

        result = api.verify_image(tmp_path)

        if result["matched"]:
            st.markdown(f"""
            <div class="match-result">
                <div style="display:flex; align-items:center; gap:12px; margin-bottom:12px;">
                    <span class="badge badge-violated" style="font-size:13px; padding:6px 16px;">MATCH FOUND</span>
                    <span style="color:#e0e0e0; font-weight:600;">Confidence: {result['confidence']*100:.0f}%</span>
                </div>
                <div class="field-label">Matched Asset</div>
                <div class="field-value">{result['asset_id']} -- {result['asset_name']}</div>
                <div class="field-label">pHash Distance</div>
                <div class="field-value">{result['phash_distance']} (threshold: 10)</div>
                <div class="field-label">Analysis</div>
                <div class="field-value">{result['details']}</div>
            </div>
            """, unsafe_allow_html=True)

            # Confidence bar
            st.progress(result["confidence"], text=f"Match confidence: {result['confidence']*100:.0f}%")
        else:
            st.markdown(f"""
            <div class="match-result no-match">
                <span class="badge badge-pending">NO MATCH</span>
                <div class="field-value" style="margin-top:12px;">{result['details']}</div>
            </div>
            """, unsafe_allow_html=True)

        # Cleanup temp file
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


# ===========================================================================
# TAB 2: Custody Trail
# ===========================================================================
with tab2:
    st.markdown('<div class="section-header">Chain of Custody</div>', unsafe_allow_html=True)

    if not assets:
        st.info("No assets available. Custody trail will appear once assets are registered.")
    else:
        asset_options_custody = {f"{a['asset_id']} -- {a['name']}": a["asset_id"] for a in assets}
        selected_custody = st.selectbox(
            "Select asset to view custody trail",
            options=list(asset_options_custody.keys()),
            key="custody_select"
        )
        custody_asset_id = asset_options_custody[selected_custody]
        trail = load_custody(custody_asset_id)

        if not trail:
            st.info("No custody events recorded for this asset.")
        else:
            # Summary row
            licensed_count = sum(1 for e in trail if e["event_type"] == "licensed")
            distributed_count = sum(1 for e in trail if e["event_type"] == "distributed")
            violated_count = sum(1 for e in trail if e["event_type"] == "violated")

            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="label">Licensed</div>
                    <div class="value green">{licensed_count}</div>
                </div>
                """, unsafe_allow_html=True)
            with c2:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="label">Distributed</div>
                    <div class="value blue">{distributed_count}</div>
                </div>
                """, unsafe_allow_html=True)
            with c3:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="label">Violations</div>
                    <div class="value red">{violated_count}</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("")

            # HMAC verification
            import hmac as hmac_module
            import hashlib as hashlib_module
            HMAC_KEY = b"digital_asset_protection_secret_2026"

            def verify_entry_hmac(entry):
                fields = [entry["asset_id"], entry["event_type"],
                          entry["recipient"], entry["notes"], entry["timestamp"]]
                message = "|".join(str(f) for f in fields)
                expected = hmac_module.new(HMAC_KEY, message.encode(), hashlib_module.sha256).hexdigest()
                return hmac_module.compare_digest(expected, entry.get("hmac_sig", ""))

            # Timeline view
            st.markdown('<div class="section-header">Event Timeline</div>', unsafe_allow_html=True)

            for entry in trail:
                hmac_ok = verify_entry_hmac(entry)
                event_class = entry["event_type"]
                badge_class = f"badge-{entry['event_type']}"
                hmac_badge = "badge-verified" if hmac_ok else "badge-violated"
                hmac_text = "VERIFIED" if hmac_ok else "TAMPERED"

                st.markdown(f"""
                <div class="timeline-item {event_class}">
                    <div class="t-time">{entry['timestamp']}</div>
                    <div class="t-event">
                        <span class="badge {badge_class}">{entry['event_type'].upper()}</span>
                        &nbsp;&nbsp;
                        <span class="badge {hmac_badge}">HMAC: {hmac_text}</span>
                    </div>
                    <div class="t-detail">
                        <strong>Recipient:</strong> {entry.get('recipient', 'N/A')}
                    </div>
                    <div class="t-detail">
                        <strong>Notes:</strong> {entry.get('notes', 'None')}
                    </div>
                    <div class="t-detail" style="margin-top:4px;">
                        <span style="color:#8892b0; font-size:10px; font-family:monospace;">
                            HMAC: {entry.get('hmac_sig', 'N/A')[:32]}...
                        </span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # Raw data table
            with st.expander("View raw custody data"):
                df_custody = pd.DataFrame(trail)
                st.dataframe(df_custody, use_container_width=True, hide_index=True)


# ===========================================================================
# TAB 3: Leak Map
# ===========================================================================
with tab3:
    st.markdown('<div class="section-header">Honeypot Leak Map</div>', unsafe_allow_html=True)

    if not baits:
        st.info("No bait assets deployed yet. Waiting for Person B's module.")
    else:
        # Bait overview table
        bait_display = []
        for b in baits:
            status = "DETECTED" if b.get("detected_at") else "PENDING"
            bait_display.append({
                "Bait ID": b["bait_id"],
                "Source Asset": b["source_asset"],
                "Seeded To": b["seeded_to"],
                "Seeded At": b["seeded_at"],
                "Status": status,
                "Detected At": b.get("detected_at") or "--",
                "Detected In": b.get("detected_in") or "--",
            })

        df_baits = pd.DataFrame(bait_display)
        st.dataframe(
            df_baits,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Bait ID": st.column_config.TextColumn("Bait ID", width="small"),
                "Source Asset": st.column_config.TextColumn("Source Asset", width="medium"),
                "Seeded To": st.column_config.TextColumn("Seeded To", width="medium"),
                "Seeded At": st.column_config.TextColumn("Seeded At", width="small"),
                "Status": st.column_config.TextColumn("Status", width="small"),
                "Detected At": st.column_config.TextColumn("Detected At", width="small"),
                "Detected In": st.column_config.TextColumn("Detected In", width="small"),
            }
        )

        # Bait detail
        st.markdown('<div class="section-header">Bait Detail & Propagation</div>', unsafe_allow_html=True)

        bait_options = {f"{b['bait_id']} -- {b['source_asset']}": b["bait_id"] for b in baits}
        selected_bait = st.selectbox(
            "Select bait to inspect",
            options=list(bait_options.keys()),
            key="bait_detail_select"
        )
        bait_id = bait_options[selected_bait]
        leak_trail = load_leak_trail(bait_id)

        if leak_trail:
            # Status and metrics
            status = leak_trail["status"]
            status_badge = "badge-detected" if status == "detected" else "badge-pending"

            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"""
                <div class="detail-card">
                    <div class="field-label">Bait ID</div>
                    <div class="field-value">{leak_trail['bait_id']}</div>
                    <div class="field-label">Source Asset</div>
                    <div class="field-value">{leak_trail['source_asset']}</div>
                    <div class="field-label">Seeded To</div>
                    <div class="field-value">{leak_trail['seeded_to']}</div>
                    <div class="field-label">Seeded At</div>
                    <div class="field-value">{leak_trail['seeded_at']}</div>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                detection_time = leak_trail.get('detected_at') or 'Not yet detected'
                detection_channel = leak_trail.get('detected_in') or '--'
                ttd = leak_trail.get('time_to_detection_minutes')
                ttd_display = f"{ttd} minutes" if ttd else '--'

                st.markdown(f"""
                <div class="detail-card">
                    <div class="field-label">Status</div>
                    <div class="field-value"><span class="badge {status_badge}">{status.upper()}</span></div>
                    <div class="field-label">First Detection</div>
                    <div class="field-value">{detection_time}</div>
                    <div class="field-label">Detected In</div>
                    <div class="field-value">{detection_channel}</div>
                    <div class="field-label">Time to Detection</div>
                    <div class="field-value">{ttd_display}</div>
                </div>
                """, unsafe_allow_html=True)

            # Propagation chain
            spread = leak_trail.get("spread_log", [])
            if spread:
                st.markdown('<div class="section-header">Propagation Chain</div>', unsafe_allow_html=True)

                chain_html = '<div class="prop-chain">'
                for i, hop in enumerate(spread):
                    type_color = {
                        "first_detection": "#ff6b6b",
                        "reshare": "#ffa94d",
                        "cross_platform": "#6cb4ee",
                    }.get(hop.get("type", ""), "#8892b0")

                    time_str = hop.get("time", "Unknown")
                    # Format time for display
                    try:
                        dt = datetime.fromisoformat(time_str)
                        time_display = dt.strftime("%H:%M")
                    except (ValueError, TypeError):
                        time_display = time_str

                    chain_html += f"""
                    <div class="prop-node">
                        <div class="node-channel">{hop.get('channel', 'Unknown')}</div>
                        <div class="node-time">{time_display}</div>
                        <div class="node-type" style="color:{type_color};">{hop.get('type', 'unknown').replace('_', ' ')}</div>
                    </div>
                    """
                    if i < len(spread) - 1:
                        chain_html += '<div class="prop-arrow">--></div>'

                chain_html += '</div>'
                st.markdown(chain_html, unsafe_allow_html=True)

                # Detection timeline table
                st.markdown('<div class="section-header">Detection Timeline</div>', unsafe_allow_html=True)

                timeline_data = []
                for hop in spread:
                    timeline_data.append({
                        "Time": hop.get("time", "Unknown"),
                        "Channel": hop.get("channel", "Unknown"),
                        "Event Type": hop.get("type", "unknown").replace("_", " ").title(),
                    })

                df_timeline = pd.DataFrame(timeline_data)
                st.dataframe(df_timeline, use_container_width=True, hide_index=True)
            else:
                st.info("No propagation data available. Bait has not been detected yet.")

            # Raw spread log
            with st.expander("View raw spread log (JSON)"):
                st.json(spread)
