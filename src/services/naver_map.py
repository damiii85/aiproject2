"""네이버 Dynamic Map 임베드. 서버용 Secret은 브라우저에 전달하지 않는다."""

import json
import math
import os
import uuid
from urllib.parse import urlencode

from dotenv import load_dotenv
from src.services.spot_catalog import BASE_DIR


def map_html(client_id, latitude, longitude, markers=None, radius=None, zoom=14):
    if not client_id or not all(math.isfinite(float(v)) for v in (latitude, longitude)):
        raise ValueError("지도 Client ID와 올바른 좌표가 필요합니다.")
    # 사용자 문자열을 HTML이나 JS 소스로 결합하지 않고 JSON 데이터로 전달한다.
    payload = json.dumps({"lat": float(latitude), "lon": float(longitude),
                          "markers": markers or [], "radius": radius, "zoom": zoom},
                         ensure_ascii=True).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    script_url = "https://oapi.map.naver.com/openapi/v3/maps.js?" + urlencode({"ncpKeyId": client_id})
    map_id = "spotcheck-map-" + uuid.uuid4().hex
    return """<div id="MAP_ID" style="height:420px;width:100%" role="region" aria-label="분석 위치 지도"></div>
<div id="MAP_ID-status" class="spotcheck-map-status" role="status">네이버 지도를 불러오는 중입니다.</div>
<script>
(function(){
const data=PAYLOAD;
const status=document.getElementById('MAP_ID-status');
let initialized=false;
window.navermap_authFailure=function(){
 document.querySelectorAll('.spotcheck-map-status').forEach(function(element){
  element.textContent='지도 인증에 실패했습니다. Client ID와 등록한 서비스 URL을 확인해 주세요.';
 });
};
function initMap(){
 try {
 const center=new naver.maps.LatLng(data.lat,data.lon);
 const map=new naver.maps.Map('MAP_ID',{center:center,zoom:data.zoom,zoomControl:true});
 const bounds=new naver.maps.LatLngBounds(center,center);
 const points=data.markers.length?data.markers:[{lat:data.lat,lon:data.lon,label:'선택 스팟'}];
 for(const item of points){
  const position=new naver.maps.LatLng(item.lat,item.lon);
  const marker=new naver.maps.Marker({map:map,position:position,title:String(item.label||'후보지')});
  bounds.extend(position);
  if(data.radius){new naver.maps.Circle({map:map,center:position,radius:data.radius,strokeColor:'#2563eb',strokeOpacity:0.6,fillColor:'#2563eb',fillOpacity:0.08});}
  const label=document.createElement('div');label.style.padding='10px';label.textContent=String(item.label||'후보지');
  const info=new naver.maps.InfoWindow({content:label});
  naver.maps.Event.addListener(marker,'click',function(){info.open(map,marker);});
 }
 if(points.length>1){map.fitBounds(bounds);}
 status.textContent='마커를 누르면 위치 이름을 확인할 수 있습니다.';
 initialized=true;
 } catch(error) {
  status.textContent='지도 초기화에 실패했습니다. 페이지를 새로고침해 주세요.';
 }
}
if(!window.__spotcheckNaverSDK){
 window.__spotcheckNaverSDK=new Promise(function(resolve,reject){
  if(window.naver && window.naver.maps){resolve();return;}
  const script=document.createElement('script');
  script.src=SCRIPT_URL;
  script.onload=resolve;
  script.onerror=reject;
  document.head.appendChild(script);
 });
}
window.__spotcheckNaverSDK.then(initMap).catch(function(){
 status.textContent='네이버 지도에 연결하지 못했습니다. 네트워크를 확인해 주세요.';
 delete window.__spotcheckNaverSDK;
});
setTimeout(function(){if(!initialized){status.textContent='지도를 표시하지 못했습니다. 인증 설정과 네트워크를 확인해 주세요.';}},12000);
})();
</script>""".replace("SCRIPT_URL", json.dumps(script_url)).replace("MAP_ID", map_id).replace("PAYLOAD", payload)


def render_map(latitude, longitude, markers=None, radius=None, zoom=14):
    import streamlit as st
    load_dotenv(BASE_DIR / ".env", override=True)
    client_id = (os.getenv("NAVER_MAP_CLIENT_ID", "").strip()
                 or os.getenv("NAVER_CLIENT_ID", "").strip())
    if not client_id:
        st.info("네이버 지도 연결 준비 중입니다. 지도 인증 설정 후 이 위치에 표시됩니다.")
        return
    # SDK 인증은 현재 페이지 URL을 사용하므로 about:srcdoc iframe에 넣지 않는다.
    # 실행 코드는 고정 템플릿이며 외부 문자열은 이스케이프한 JSON 데이터로만 전달한다.
    st.html(map_html(client_id, latitude, longitude, markers, radius, zoom),
            unsafe_allow_javascript=True)
