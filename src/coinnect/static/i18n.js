// Coinnect i18n — 15 languages
const LANGS={
  en:{name:'English',dir:'ltr',flag:'🇺🇸'},
  es:{name:'Español',dir:'ltr',flag:'🇲🇽'},
  pt:{name:'Português',dir:'ltr',flag:'🇧🇷'},
  fr:{name:'Français',dir:'ltr',flag:'🇫🇷'},
  ar:{name:'العربية',dir:'rtl',flag:'🇸🇦'},
  hi:{name:'हिन्दी',dir:'ltr',flag:'🇮🇳'},
  bn:{name:'বাংলা',dir:'ltr',flag:'🇧🇩'},
  id:{name:'Indonesia',dir:'ltr',flag:'🇮🇩'},
  ja:{name:'日本語',dir:'ltr',flag:'🇯🇵'},
  de:{name:'Deutsch',dir:'ltr',flag:'🇩🇪'},
  tl:{name:'Filipino',dir:'ltr',flag:'🇵🇭'},
  vi:{name:'Tiếng Việt',dir:'ltr',flag:'🇻🇳'},
  th:{name:'ภาษาไทย',dir:'ltr',flag:'🇹🇭'},
  sw:{name:'Kiswahili',dir:'ltr',flag:'🇰🇪'},
  ur:{name:'اردو',dir:'rtl',flag:'🇵🇰'},
  'zh-CN':{name:'简体中文',dir:'ltr',flag:'🇨🇳'},
  'zh-TW':{name:'繁體中文',dir:'ltr',flag:'🇹🇼'},
};

const I18N={
en:{
  nav_api:'API docs',nav_whitepaper:'Whitepaper',nav_pricing:'Pricing',nav_support:'❤️ Support',
  hero_h1:'The free open map for <span class="gradient-text">global money</span>',
  hero_sub:'The cheapest path between any two currencies — fiat, crypto, P2P. Standard. Free. Open. For humans & bots.',
  for_humans:'For humans',for_agents:'For AI agents',
  h_1:'→ Pick currencies & amount',h_2:'→ Compare all routes instantly',
  h_3:'→ See step-by-step instructions',h_4:'→ Know exactly how much arrives',
  label_amount:'Amount',label_from:'From',label_to:'To',btn_find:'Find routes →',
  quickstart:'Agent / API quickstart',
  filter_label:'Filter:',filter_all:'All',filter_cheap:'Best rate first',
  filter_fast:'Fastest first',filter_nocrypto:'Fiat only',filter_crypto:'Crypto routes',
  hist_title:'Rate history',hist_nodata:'Not enough data yet.',
  loading:'Checking exchanges in real time...',
  you_send:'You send',they_receive:'They receive',rate:'Rate:',
  steps_reqs:'Rate origin',sender_needs:'Sender needs',recipient_needs:'Recipient needs',
  no_reqs:'No special requirements',more_options:'More options',best_badge:'Best',tag_cheapest:'Best rate',tag_fastest:'Fastest',
  fees_pct:'% fees',no_filter_routes:'No routes match this filter',
  footer_note:'Coinnect shows routes — it never executes transfers or holds funds. Each exchange handles its own KYC.',
  live_rates:'Live rates',rates_ago:'Rates {sec}s ago',
  error_try:'Try a different pair or check back in a moment',
  save_vs_wu:'Save ~{from} {saved} vs Western Union',best_route:'Best route',
  pricing_title:'<s>Pricing</s>',
  pricing_sub:'Free.<sup class="text-cyan-500 font-bold">*</sup> No credit card. No sign-up. No affiliate fees — ever.',
  anon:'Anonymous',anon_sub:'No key needed',builder:'Builder',builder_sub:'Self-serve key · no signup',
  selfhost:'Self-hosted',selfhost_sub:'MIT license · deploy anywhere',
  most_popular:'Most popular',get_key:'Get free API key →',
  free_forever_note:'Coinnect is free for everyone — humans and bots. Fair use limits apply. We commit to keeping a free tier while the service exists. Limits may be adjusted with 90 days notice. Open source (MIT).',
  support_free:'Free because of',donor_link:'donor support ❤️',
  donate_title:'Keep Coinnect free & unbiased',
  donate_sub:'No affiliate fees. No ads. No investors. We show the best route — not the most profitable one for us. Mission-driven · no affiliate fees · If this saved you money, consider supporting the project.',
  crypto_soon:'Crypto donations coming soon (ETH / USDC / BTC).',
  sponsor_gh:'❤️ Sponsor on GitHub',buy_coffee:'☕ Buy me a coffee',read_wp:'📄 Read the whitepaper',
  view_gh:'View on GitHub →',
  open_source:'Open protocol · MIT license · Mission-driven · Mapping the money rails of the internet',
  footer_rates:'Rates refresh every 3 min',footer_nofunds:'Coinnect never holds your funds',
  footer_notrack:'Disable tracking',footer_disclaimer:'Disclaimer',cookie_understood:'Understood',
  cookie_text:'We use Google Analytics to understand how people use Coinnect. No personal data is sold.',
  cookie_decline:'Decline analytics',cookie_accept:'Accept',
  disc_title:'Disclaimer & Terms of Use',
  disc_rate_h:'Rate accuracy',
  disc_rate:'Exchange rates and fees shown on Coinnect are sourced from provider APIs and published pricing pages. Rates update approximately every 3 minutes for live sources. For providers without a public API, fees are based on published pricing and marked with "~est." — these are estimates and may not reflect the exact rate you will receive.',
  disc_liability_h:'No liability',
  disc_liability:'Coinnect is an information service only. We do not execute transfers, hold funds, or act as a financial intermediary. We make no warranty, express or implied, about the accuracy, completeness, or timeliness of the rates displayed. Any financial decision made based on information shown on this site is at your sole risk. Coinnect and its operators accept no responsibility or liability for any loss or damage arising from reliance on this information.',
  disc_verify_h:'Always verify',
  disc_verify:'Before executing any transfer, verify the current rate and fees directly with the provider on their official website or app. Rates can change in seconds, and providers may apply different fees based on your account type, payment method, or jurisdiction.',
  disc_analytics_h:'Analytics & cookies',
  disc_analytics:'We use Google Analytics (GA4) to understand aggregate usage patterns. No personal financial data is transmitted to GA4. You can opt out at any time by visiting <a href="/?notrack" class="text-cyan-600 dark:text-cyan-400 underline">coinnect.bot/?notrack</a> or by clicking "Decline analytics" on the cookie banner.',
  disc_affil_h:'No affiliation or endorsement',
  disc_affil:'Coinnect is not affiliated with, endorsed by, or sponsored by any of the providers listed. Provider names and logos are trademarks of their respective owners, used solely for identification purposes. Any analogies or category comparisons used on this site (e.g. "navigation app for money", "GPS for transfers") are illustrative descriptions only and do not imply any relationship with, or endorsement by, any specific company or product.',
  close:'Close',key_title:'Get your API key',key_sub:'No email. No account. Instant.',
  key_label:'Label (optional)',key_gen:'Generate key',key_generating:'Generating…',
  key_save:'Save this key — it cannot be recovered. Use it as:',
  key_copy:'⎘ Copy to clipboard',key_copied:'✓ Copied!',key_error:'Failed to generate key. Please try again.',
  sender_badge:'Sender',recipient_badge:'Recipient',via_word:'via',suggest_provider:'+ Suggest a provider',
  report_bug:'🐛 Report bug',suggest_corridor:'+ Suggest corridor',
  bug_title:'Report a bug',bug_placeholder:'What happened? Which currencies? What did you expect?',
  bug_rate_q:'Is this a rate error?',bug_rate_select:'Which route looks wrong?',
  corridor_title:'Suggest a corridor',corridor_from:'From (e.g. USD)',corridor_to:'To (e.g. PKR)',
  corridor_note:'Note (optional)',submit:'Submit',cancel:'Cancel',thanks:'Thanks! We\'ll look into it.',
  miguel_p1:'This started as my unemployment project. It\'s still maintained by one person — me, Miguel.',
  miguel_p2:'If this grew useful to you and you\'d like to help connect me with a foundation or institution that supports open financial infrastructure, I\'d love to hear from you. <a href="mailto:miguel@coinnect.bot" class="text-cyan-500 hover:underline">miguel@coinnect.bot</a> · Have a nice day (or night, wherever you are). 🌍',
  miguel_ps:'P.S. — I\'d also love to get involved in a forestry project. I genuinely love nature. If you have a piece of land you\'d like to replant, reach out — let\'s think of a plan to get the resources together. 🌱',
  step_convert:'Convert {from} to {to} via {via}',step_you_give:'You give: {amount} {currency}',step_you_get:'You get: ≈{amount} {currency}',step_fee:'Fee: {fee}%',step_time:'Time: ≈{time}',
  ds_title:'30+ data sources',ds_sub:'Every search checks all sources. No affiliate fees, no hidden markup.',
  badge_live:'LIVE RATE',badge_live_desc:'Exchange API, refreshed ~3 min',
  badge_official:'OFFICIAL',badge_official_desc:'Central bank / country rate',
  badge_reference:'REFERENCE',badge_reference_desc:'Market data aggregator',
  badge_estimated:'ESTIMATED',badge_estimated_desc:'Published fee tables',
  cat_live:'Live',cat_official:'Official',cat_reference:'Reference',cat_estimated:'Estimated',
  rate_correct:'Was this rate correct?',rate_feedback:'Rate feedback',
  fb_correct:'Rate was accurate',fb_too_high:'Shown rate too high',fb_too_low:'Shown rate too low',
  fb_provider_down:'Provider unavailable',fb_fee_wrong:'Fee was different',fb_other:'Other issue',
  fb_thanks:'Thanks for the feedback!',fb_note:'Optional note',
  read_more:'Read more — data sources & refresh rates',fee_source:'Published fees',
  similar_cost:'Similar cost',n_routes:'{n} routes',
  step_narrative_send:'Send',step_narrative_then:'Then give',step_narrative_finally:'Finally, send',
  step_narrative_receive:'receive',step_narrative_in:'in',step_by_step:'Step by step',
  key_error_rate:'Too many keys created from your connection. Try again in an hour.',key_error_net:"Couldn't reach the server. Check your connection and try again.",
}
};
const TAGLINES={
  en:['The way to find the cheapest way to move money 🌍','A navigation app for your money 🗺️','Find the cheapest lane, every time ⚡','Your money\'s GPS — no bank detours 🛰️','Like a flight search engine, but for remittances ✈️'],
  es:['El GPS de tu dinero 🗺️','La manera de encontrar la ruta más barata para mover dinero 🌍','Encuentra el carril más barato, siempre ⚡','Como un buscador de vuelos, pero para remesas ✈️','Sin rodeos bancarios — solo la ruta directa 🏦'],
  pt:['O GPS do seu dinheiro 🗺️','O mapa de rotas para transferências globais 🛰️','Encontre a rota mais barata, sempre ⚡','Como um buscador de voos, mas para remessas ✈️','Sem desvios bancários 🏦'],
  fr:['Le GPS de votre argent 🗺️','La carte de routes pour vos transferts 🛰️','Trouvez le chemin le moins cher ⚡','Comme un comparateur de vols, pour les virements ✈️','Zéro détour bancaire 🏦'],
  ar:['نظام GPS لأموالك 🗺️','خريطة التحويلات الدولية 🛰️','ابحث عن أرخص طريق دائماً ⚡','كمحرك بحث الرحلات، لكن للتحويلات المالية ✈️','بلا تعقيدات بنكية 🏦'],
  hi:['आपके पैसों का GPS 🗺️','अंतर्राष्ट्रीय ट्रांसफर का रूटिंग मैप 🛰️','हमेशा सबसे सस्ता रास्ता खोजें ⚡','फ्लाइट सर्च इंजन जैसा, रेमिटेंस के लिए ✈️','बैंक के चक्करों से आज़ादी 🏦'],
  bn:['আপনার অর্থের GPS 🗺️','আন্তর্জাতিক ট্রান্সফারের রুটিং ম্যাপ 🛰️','সবচেয়ে সস্তা পথ খুঁজুন ⚡','ফ্লাইট সার্চ ইঞ্জিনের মতো, রেমিট্যান্সের জন্য ✈️','ব্যাংকের ঝামেলা ছাড়া 🏦'],
  id:['GPS untuk uangmu 🗺️','Peta rute untuk transfer internasional 🛰️','Temukan jalur termurah, selalu ⚡','Seperti mesin pencari penerbangan, untuk kirim uang ✈️','Tanpa detour bank 🏦'],
  ja:['あなたのお金のGPS 🗺️','海外送金のルーティングマップ 🛰️','常に最安値ルートを発見 ⚡','フライト検索エンジンの国際送金版 ✈️','銀行の回り道なし 🏦'],
  de:['Das GPS für Ihr Geld 🗺️','Die Routenkarte für internationale Überweisungen 🛰️','Immer die günstigste Route finden ⚡','Wie eine Flugsuchmaschine, für Geldtransfers ✈️','Kein Bankumweg mehr 🏦'],
  tl:['Ang GPS ng iyong pera 🗺️','Mapa ng ruta para sa international na padala 🛰️','Palaging pinakamura ang ruta ⚡','Parang flight search engine, para sa remittance ✈️','Walang bank detour 🏦'],
  vi:['GPS cho tiền của bạn 🗺️','Bản đồ định tuyến cho chuyển tiền quốc tế 🛰️','Luôn tìm tuyến rẻ nhất ⚡','Như công cụ tìm vé máy bay, cho kiều hối ✈️','Không vòng vèo qua ngân hàng 🏦'],
  th:['GPS สำหรับเงินของคุณ 🗺️','แผนที่เส้นทางการโอนเงินระหว่างประเทศ 🛰️','ค้นหาเส้นทางถูกที่สุดเสมอ ⚡','เหมือนเครื่องมือค้นหาตั๋วบิน สำหรับส่งเงิน ✈️','ไม่มีทางอ้อมผ่านธนาคาร 🏦'],
  sw:['GPS ya pesa yako 🗺️','Ramani ya njia za uhamisho wa kimataifa 🛰️','Pata njia nafuu zaidi kila wakati ⚡','Kama injini ya kutafuta ndege, kwa kutuma pesa ✈️','Bila vikwazo vya benki 🏦'],
  ur:['آپ کے پیسوں کا GPS 🗺️','بین الاقوامی ٹرانسفر کا روٹنگ نقشہ 🛰️','ہمیشہ سستا ترین راستہ تلاش کریں ⚡','فلائٹ سرچ انجن جیسا، رقم بھیجنے کے لیے ✈️','بینک کے چکروں سے آزادی 🏦'],
};

// Miguel's PS — forestry note. Spanish: natural paragraph. All others: shown as a quote.
const MIGUEL_PS={
  es:'P.D. — También me encantaría meterme en algún proyecto forestal. Me encanta la naturaleza. Si tienes un terreno que quieras reforestar, escríbeme — y vemos juntos cómo conseguimos los recursos. 🌱',
  en:'P.S. — I\'d also love to get involved in a forestry project. I genuinely love nature. If you have a piece of land you\'d like to replant, reach out — let\'s think of a plan to get the resources together. 🌱',
  pt:'"Também adoraria me envolver em um projeto florestal. Adoro a natureza. Se você tem um terreno que gostaria de reflorestar, entre em contato — vamos pensar juntos em um plano para conseguir os recursos. 🌱"',
  fr:'"Je rêve aussi de m\'impliquer dans un projet de reboisement. J\'aime profondément la nature. Si vous avez un terrain que vous souhaitez replanter, contactez-moi — réfléchissons ensemble à la façon d\'obtenir les ressources. 🌱"',
  ar:'"أتمنّى أيضاً الانخراط في مشروع تشجير. أحبّ الطبيعة حقاً. إن كان لديك أرض تودّ زراعتها من جديد، تواصل معي — لنفكّر معاً في كيفية تأمين الموارد اللازمة. 🌱"',
  hi:'"मैं वनीकरण के किसी प्रोजेक्ट में भी शामिल होना चाहूँगा। मुझे सच में प्रकृति से बहुत प्यार है। अगर आपके पास कोई ज़मीन है जिसे आप दोबारा हरा-भरा करना चाहते हैं, तो संपर्क करें — मिलकर सोचते हैं कि संसाधन कैसे जुटाएँ। 🌱"',
  bn:'"আমি একটি বনায়ন প্রকল্পে জড়িত হতেও ভালোবাসব। আমি সত্যিই প্রকৃতিকে ভালোবাসি। যদি আপনার কাছে এমন জমি থাকে যেখানে আবার গাছ লাগাতে চান, যোগাযোগ করুন — একসাথে ভাবি কীভাবে সম্পদ জোগাড় করা যায়। 🌱"',
  id:'"Saya juga ingin sekali terlibat dalam proyek kehutanan. Saya benar-benar mencintai alam. Jika kamu punya lahan yang ingin dihijaukan kembali, hubungi saya — ayo kita pikirkan bersama bagaimana mendapatkan sumber dayanya. 🌱"',
  ja:'"森林プロジェクトにも関わりたいと思っています。自然が本当に大好きです。再植林したい土地があれば、ぜひ連絡してください — 一緒にリソースの調達方法を考えましょう。 🌱"',
  de:'"Ich würde mich auch sehr gerne an einem Forstprojekt beteiligen. Ich liebe die Natur wirklich. Wenn du ein Stück Land hast, das du wieder bepflanzen möchtest, melde dich — lass uns gemeinsam überlegen, wie wir die Mittel dafür bekommen. 🌱"',
  tl:'"Gusto ko ring lubos na makisali sa isang proyektong pangkagubatan. Talagang mahal ko ang kalikasan. Kung mayroon kang lupang gustong muling itaniman, makipag-ugnayan sa akin — mag-isip tayo nang magkasama kung paano makukuha ang mga mapagkukunan. 🌱"',
  vi:'"Tôi cũng rất muốn tham gia một dự án lâm nghiệp. Tôi thực sự yêu thiên nhiên. Nếu bạn có mảnh đất muốn trồng lại cây, hãy liên hệ — cùng nhau nghĩ cách huy động nguồn lực. 🌱"',
  th:'"ฉันอยากมีส่วนร่วมในโครงการด้านป่าไม้ด้วย ฉันรักธรรมชาติอย่างจริงใจ ถ้าคุณมีที่ดินที่อยากปลูกต้นไม้ใหม่ ติดต่อมาได้เลย — มาช่วยกันคิดแผนหาทรัพยากรด้วยกัน 🌱"',
  sw:'"Ningependa pia kushiriki katika mradi wa misitu. Napenda sana asili. Kama una kipande cha ardhi unachotaka kupanda miti tena, nipigie — tufikirien pamoja jinsi ya kupata rasilimali. 🌱"',
  ur:'"میں جنگلاتی منصوبے میں بھی شامل ہونا چاہوں گا۔ مجھے فطرت سے سچ میں بہت محبت ہے۔ اگر آپ کے پاس ایسی زمین ہے جسے آپ دوبارہ سرسبز کرنا چاہتے ہیں، رابطہ کریں — مل کر سوچتے ہیں کہ وسائل کہاں سے لائیں۔ 🌱"',
};

function _renderMiguelPs(){
  const el=document.getElementById('miguelPs');
  if(!el)return;
  const txt=MIGUEL_PS[_lang]||MIGUEL_PS.en;
  if(_lang==='es'){
    el.innerHTML=`<p class="text-xs text-gray-400 dark:text-gray-500 mt-1">${txt}</p>`;
  } else {
    el.innerHTML=`<blockquote class="border-l-2 border-gray-300 dark:border-gray-600 pl-3 italic text-xs text-gray-400 dark:text-gray-500">${txt}</blockquote>`;
  }
}

let _taglineIdx=0,_taglineTimer=null;
function initTaglineRotator(){
  const el=document.getElementById('taglineRotator');
  if(!el)return;
  const phrases=(TAGLINES[_lang]||TAGLINES.en);
  _taglineIdx=Math.floor(Math.random()*phrases.length);
  el.textContent=phrases[_taglineIdx];
  el.style.opacity='1';
  el.style.transition='opacity 0.5s';
  if(_taglineTimer)clearInterval(_taglineTimer);
  _taglineTimer=setInterval(()=>{
    el.style.opacity='0';
    setTimeout(()=>{
      const ps=(TAGLINES[_lang]||TAGLINES.en);
      _taglineIdx=(_taglineIdx+1)%ps.length;
      el.textContent=ps[_taglineIdx];
      el.style.opacity='1';
    },500);
  },3500);
}

// ── Core i18n functions ────────────────────────────────────────────────────
let _lang='en';
const _I18N_V='2026.11.02.1';

function t(key){return(I18N[_lang]||I18N.en)[key]||I18N.en[key]||key;}

// English is built in; other languages load on demand. If one fails to load,
// t() falls back to English.
function _loadLang(code,done){
  if(I18N[code]){done();return;}
  const s=document.createElement('script');
  s.src=`/static/i18n/${code}.js?v=${_I18N_V}`;
  s.onload=done;
  s.onerror=done;
  document.head.appendChild(s);
}

let _cjkFontLoaded=false;
function _ensureCjkFont(code){
  if(_cjkFontLoaded||!['zh-CN','zh-TW','ja'].includes(code))return;
  _cjkFontLoaded=true;
  const l=document.createElement('link');
  l.rel='stylesheet';
  l.href='https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;700&family=Noto+Sans+TC:wght@400;700&display=swap';
  document.head.appendChild(l);
}

function _refreshLangUI(){
  applyLang();
  initTaglineRotator();
  // Re-render dynamic content if results exist
  if(typeof _allRoutes!=='undefined'&&_allRoutes.length&&_fromCur&&_toCur){
    renderResults(_allRoutes,_fromCur,_toCur);
  }
  // Update hist title
  const ht=document.getElementById('histTitle');
  if(ht)ht.textContent=t('hist_title');
}

function setLang(code){
  if(!LANGS[code])return;
  localStorage.setItem('coinnect_lang',code);
  // Close dropdown
  const dd=document.getElementById('langDropdown');
  if(dd)dd.classList.add('hidden');
  _ensureCjkFont(code);
  _loadLang(code,()=>{
    _lang=code;
    document.documentElement.lang=code;
    document.documentElement.dir=LANGS[code].dir;
    _refreshLangUI();
  });
}

function applyLang(){
  // data-i18n → textContent
  document.querySelectorAll('[data-i18n]').forEach(el=>{
    const k=el.dataset.i18n;
    const v=t(k);
    if(v&&v!==k)el.textContent=v;
  });
  // data-i18n-html → innerHTML
  document.querySelectorAll('[data-i18n-html]').forEach(el=>{
    const k=el.dataset.i18nHtml;
    const v=t(k);
    if(v&&v!==k)el.innerHTML=v;
  });
  // Update lang picker label
  const btn=document.getElementById('langBtn');
  if(btn)btn.innerHTML=`${LANGS[_lang].flag} <span class="hidden sm:inline">${LANGS[_lang].name}</span> <span class="text-gray-400 text-xs">▾</span>`;
  // Render Miguel's PS in current language
  _renderMiguelPs();
}

// Country → dominant language mapping (ISO 3166-1 alpha-2 → LANGS key)
const COUNTRY_LANG={
  // Spanish
  MX:'es',GT:'es',HN:'es',SV:'es',NI:'es',CR:'es',PA:'es',
  CO:'es',VE:'es',EC:'es',PE:'es',BO:'es',CL:'es',PY:'es',
  UY:'es',AR:'es',CU:'es',DO:'es',PR:'es',GQ:'es',ES:'es',
  // Portuguese
  BR:'pt',PT:'pt',AO:'pt',MZ:'pt',CV:'pt',GW:'pt',ST:'pt',TL:'pt',
  // French
  FR:'fr',BE:'fr',SN:'fr',CI:'fr',ML:'fr',BF:'fr',NE:'fr',
  GN:'fr',MG:'fr',CM:'fr',TD:'fr',CF:'fr',CG:'fr',CD:'fr',
  GA:'fr',BJ:'fr',TG:'fr',BI:'fr',DJ:'fr',KM:'fr',HT:'fr',
  // Arabic
  SA:'ar',AE:'ar',EG:'ar',IQ:'ar',SY:'ar',JO:'ar',LB:'ar',
  KW:'ar',BH:'ar',QA:'ar',OM:'ar',YE:'ar',LY:'ar',TN:'ar',
  DZ:'ar',MA:'ar',SD:'ar',MR:'ar',SO:'ar',PS:'ar',
  // Hindi
  IN:'hi',
  // Bengali
  BD:'bn',
  // Indonesian
  ID:'id',
  // Japanese
  JP:'ja',
  // German
  DE:'de',AT:'de',LI:'de',
  // Filipino
  PH:'tl',
  // Vietnamese
  VN:'vi',
  // Thai
  TH:'th',
  // Swahili
  KE:'sw',TZ:'sw',UG:'sw',RW:'sw',
  // Urdu
  PK:'ur',
  // Chinese
  CN:'zh-CN',TW:'zh-TW',HK:'zh-TW',MO:'zh-TW',SG:'zh-CN',
};

// Country → flag for Spanish-speaking countries
const ES_COUNTRY_FLAG={
  MX:'🇲🇽',GT:'🇬🇹',HN:'🇭🇳',SV:'🇸🇻',NI:'🇳🇮',CR:'🇨🇷',PA:'🇵🇦',
  CO:'🇨🇴',VE:'🇻🇪',EC:'🇪🇨',PE:'🇵🇪',BO:'🇧🇴',CL:'🇨🇱',PY:'🇵🇾',
  UY:'🇺🇾',AR:'🇦🇷',CU:'🇨🇺',DO:'🇩🇴',PR:'🇵🇷',GQ:'🇬🇶',ES:'🇪🇸',
};

// Detected country code (set by geo lookup)
let _country='';

function initLang(){
  // Priority: localStorage → navigator.language → geo lookup → 'en'
  const saved=localStorage.getItem('coinnect_lang');
  if(saved&&LANGS[saved]){
    _lang=saved;
  } else {
    // Synchronous fallback: browser language
    const nav=navigator.language||'en';
    const code=nav.split('-')[0].toLowerCase();
    if(LANGS[code])_lang=code;
  }
  document.documentElement.lang=_lang;
  document.documentElement.dir=LANGS[_lang].dir;
  _ensureCjkFont(_lang);
  // The page may already have rendered in English by the time this arrives.
  if(_lang!=='en')_loadLang(_lang,_refreshLangUI);
  // Async geo-detection (runs after page loads, updates if no saved pref)
  _geoDetectLang();
}

function _geoDetectLang(){
  if(localStorage.getItem('coinnect_lang'))return;
  fetch('https://ipapi.co/json/',{signal:AbortSignal.timeout(3000)})
    .then(r=>r.json())
    .then(d=>{
      _country=(d.country_code||'').toUpperCase();
      // Update Spanish flag in picker to match visitor's country
      if(ES_COUNTRY_FLAG[_country]){
        LANGS.es.flag=ES_COUNTRY_FLAG[_country];
        _updateEsFlagBtn();
      }
      if(localStorage.getItem('coinnect_lang'))return; // user picked one meanwhile
      const lang=COUNTRY_LANG[_country];
      if(lang&&LANGS[lang]&&lang!==_lang){
        _ensureCjkFont(lang);
        _loadLang(lang,()=>{
          if(localStorage.getItem('coinnect_lang'))return; // user picked one while it loaded
          _lang=lang;
          document.documentElement.lang=_lang;
          document.documentElement.dir=LANGS[_lang].dir;
          _refreshLangUI();
        });
      }
    })
    .catch(()=>{}); // silent fail — keep browser-detected lang
}

function _updateEsFlagBtn(){
  // Update the Español button in the dropdown with the country-specific flag
  const btn=document.querySelector('#langDropdown button[onclick="setLang(\'es\')"]');
  if(btn)btn.innerHTML=`${LANGS.es.flag} Español`;
  // Update nav button if current lang is es
  if(_lang==='es'){
    const navBtn=document.getElementById('langBtn');
    if(navBtn)navBtn.innerHTML=`${LANGS.es.flag} <span class="hidden sm:inline">Español</span> <span class="text-gray-400 text-xs">▾</span>`;
  }
}

function toggleLangDropdown(){
  const dd=document.getElementById('langDropdown');
  dd.classList.toggle('hidden');
}

// Close dropdown on outside click
document.addEventListener('click',e=>{
  const picker=document.getElementById('langPicker');
  if(picker&&!picker.contains(e.target)){
    document.getElementById('langDropdown').classList.add('hidden');
  }
});
