"""Curated knowledge base: government schemes and common crop disease guidance.

Content is summarized from public agricultural extension material for a
student project. It is advisory only and must be confirmed with a local KVK
(Krishi Vigyan Kendra) or agriculture extension officer before spraying.
"""

from __future__ import annotations

SCHEMES = [
    {
        "name": "PM-KISAN",
        "category": "Income support",
        "benefit": "₹6,000 per year paid in three ₹2,000 instalments to eligible landholding farmer families.",
        "eligibility": "All landholding farmer families with cultivable land, subject to exclusion criteria.",
        "apply": "Register at pmkisan.gov.in or through a Common Service Centre (CSC) with Aadhaar, land records and bank details.",
        "link": "https://pmkisan.gov.in",
        "tags": ["All"],
    },
    {
        "name": "Pradhan Mantri Fasal Bima Yojana (PMFBY)",
        "category": "Crop insurance",
        "benefit": "Crop insurance at low farmer premium: 2% for kharif food and oilseed crops, 1.5% for rabi and 5% for commercial crops.",
        "eligibility": "Farmers growing notified crops in notified areas, including sharecroppers with valid documents.",
        "apply": "Enrol through your bank, CSC or pmfby.gov.in before the cut-off date for the season.",
        "link": "https://pmfby.gov.in",
        "tags": ["All"],
    },
    {
        "name": "Kisan Credit Card (KCC)",
        "category": "Credit",
        "benefit": "Short-term crop loan up to ₹3 lakh at a low interest rate with interest subvention for prompt repayment.",
        "eligibility": "Farmers, tenant farmers, oral lessees and self-help groups engaged in agriculture.",
        "apply": "Apply at any scheduled bank or cooperative bank with land documents, Aadhaar and passport-size photo.",
        "link": "https://www.nabard.org",
        "tags": ["All"],
    },
    {
        "name": "e-NAM",
        "category": "Marketing",
        "benefit": "Sell produce online to buyers across states through linked mandis, with transparent bidding.",
        "eligibility": "Farmers registered with a participating APMC mandi.",
        "apply": "Register on the e-NAM app or at your mandi office/CSC with Aadhaar, bank account and mobile number.",
        "link": "https://www.enam.gov.in",
        "tags": ["All"],
    },
    {
        "name": "Soil Health Card Scheme",
        "category": "Soil health",
        "benefit": "Free soil testing every two years with a card showing nutrient status and crop-wise fertiliser advice.",
        "eligibility": "All farmers with agricultural land.",
        "apply": "Contact your block agriculture office or CSC; samples are collected and tested by the state agriculture department.",
        "link": "https://soilhealth.dac.gov.in",
        "tags": ["All"],
    },
    {
        "name": "PM-KUSUM",
        "category": "Energy",
        "benefit": "Support for solar irrigation pumps and grid-connected solar power plants on farmland.",
        "eligibility": "Farmers, cooperatives and panchayats, subject to state quotas.",
        "apply": "Apply through your state renewable energy agency portal or the PM-KUSUM national portal.",
        "link": "https://pmkusum.mnre.gov.in",
        "tags": ["All"],
    },
    {
        "name": "Mission for Integrated Development of Horticulture (MIDH)",
        "category": "Horticulture",
        "benefit": "Assistance for orchards, protected cultivation, cold storage, pack houses and post-harvest handling of fruits and vegetables.",
        "eligibility": "Horticulture farmers, FPOs and entrepreneurs, subject to state norms.",
        "apply": "Apply through your state horticulture department with a project proposal and land documents.",
        "link": "https://midh.gov.in",
        "tags": ["Fruit", "Onion", "Tomato", "Potato"],
    },
    {
        "name": "Agriculture Infrastructure Fund",
        "category": "Infrastructure",
        "benefit": "Medium-term credit with interest subvention for warehouses, cold stores and primary processing units.",
        "eligibility": "Farmers, FPOs, agri-entrepreneurs and cooperatives.",
        "apply": "Apply through a lending bank; the project is registered on the AIF portal for subsidy tracking.",
        "link": "https://agriinfra.dac.gov.in",
        "tags": ["All"],
    },
    {
        "name": "10,000 Farmer Producer Organisations (FPOs)",
        "category": "Collective farming",
        "benefit": "Formation and handholding support for FPOs, including equity grant, credit guarantee and market linkage.",
        "eligibility": "Groups of farmers forming an FPO in a contiguous area.",
        "apply": "Contact SFAC, NABARD or the state FPO cell; a producer group and business plan are required.",
        "link": "https://sfac.gov.in",
        "tags": ["All"],
    },
]


DISEASES = [
    {
        "crop": "Wheat",
        "name": "Yellow rust",
        "type": "Fungal",
        "symptoms": ["Yellow stripes on leaves", "Orange-yellow powder on fingers", "Weak, stunted plants"],
        "remedy": "Spray Propiconazole 25% EC at 1 ml/litre of water when the first pustules appear. Repeat after 15 days if needed.",
        "prevention": "Grow rust-resistant varieties, sow on time and avoid excess nitrogen.",
        "keywords": ["yellow stripe", "orange powder", "rust"],
    },
    {
        "crop": "Wheat",
        "name": "Karnal bunt",
        "type": "Fungal",
        "symptoms": ["Partly black grains", "Fishy smell in grain", "Shrunken grain at harvest"],
        "remedy": "Use certified seed treated with Thiram or Carboxin. Avoid late sowing and excess irrigation at flowering.",
        "prevention": "Rotate crops, use clean seed and keep the field free of infected stubble.",
        "keywords": ["black grain", "fishy", "bunt"],
    },
    {
        "crop": "Paddy (Rice)",
        "name": "Bacterial leaf blight",
        "type": "Bacterial",
        "symptoms": ["Water-soaked streaks on leaves", "Yellow-white leaf margins", "Drying leaf tips"],
        "remedy": "Drain the field, stop excess nitrogen, and spray copper oxychloride with streptocycline at label doses.",
        "prevention": "Use resistant varieties, balanced fertiliser and clean irrigation water.",
        "keywords": ["blight", "streak", "dry leaf tip", "yellow margin"],
    },
    {
        "crop": "Paddy (Rice)",
        "name": "Rice blast",
        "type": "Fungal",
        "symptoms": ["Spindle-shaped grey lesions", "Neck rot below the panicle", "Empty or broken panicles"],
        "remedy": "Spray Tricyclazole 75% WP at 0.6 g/litre at booting stage; follow label directions.",
        "prevention": "Avoid dense sowing, keep balanced nitrogen and use blast-resistant varieties.",
        "keywords": ["blast", "spindle", "neck rot", "lesion"],
    },
    {
        "crop": "Paddy (Rice)",
        "name": "Brown planthopper",
        "type": "Pest",
        "symptoms": ["Hopperburn: circular drying patches", "Insects at the base of stems", "Honeydew and sooty mould"],
        "remedy": "Drain the field for a few days and apply Imidacloprid or Pymetrozine at recommended doses directed at the stem base.",
        "prevention": "Avoid excess nitrogen and keep alternate-row or wider spacing for airflow.",
        "keywords": ["hopper", "hopperburn", "insects", "sooty"],
    },
    {
        "crop": "Maize",
        "name": "Fall armyworm",
        "type": "Pest",
        "symptoms": ["Ragged holes in young whorls", "Moist sawdust-like frass", "Larvae with dark head inside whorl"],
        "remedy": "Handpick larvae where possible and apply Emamectin benzoate 5% SG at 0.4 g/litre into the whorl, or neem-based spray for early stages.",
        "prevention": "Sow on time, monitor pheromone traps and avoid continuous maize cropping.",
        "keywords": ["armyworm", "whorl", "larva", "frass", "holes"],
    },
    {
        "crop": "Maize",
        "name": "Turcicum leaf blight",
        "type": "Fungal",
        "symptoms": ["Long cigar-shaped grey lesions", "Brown spots on older leaves", "Premature leaf drying"],
        "remedy": "Spray Mancozeb 75% WP at 2 g/litre at first symptoms; repeat after 10-15 days if humid weather continues.",
        "prevention": "Crop rotation, resistant hybrids and removal of infected stubble.",
        "keywords": ["blight", "lesion", "cigar", "leaf spot"],
    },
    {
        "crop": "Soybean",
        "name": "Yellow mosaic",
        "type": "Viral",
        "symptoms": ["Yellow mosaic patches on leaves", "Stunted growth", "Fewer pods"],
        "remedy": "Remove infected plants and manage the whitefly vector with recommended sprays. There is no direct cure for the virus.",
        "prevention": "Use resistant varieties, timely sowing and whitefly monitoring.",
        "keywords": ["mosaic", "yellow", "whitefly", "stunted"],
    },
    {
        "crop": "Soybean",
        "name": "Soybean rust",
        "type": "Fungal",
        "symptoms": ["Small brown pustules under leaves", "Yellowing leaves", "Early leaf drop"],
        "remedy": "Spray Hexaconazole 5% EC at 1 ml/litre at first sign; repeat as per label if the weather stays humid.",
        "prevention": "Avoid dense crop, follow crop rotation and use clean seed.",
        "keywords": ["rust", "pustule", "yellow leaf", "leaf drop"],
    },
    {
        "crop": "Cotton",
        "name": "Pink bollworm",
        "type": "Pest",
        "symptoms": ["Rosette-shaped flowers", "Holes in bolls", "Pink larvae inside bolls"],
        "remedy": "Install pheromone traps, remove rosette flowers and use recommended bollworm insecticides such as chlorantraniliprole at label dose.",
        "prevention": "Follow refuge planting, avoid late crop extension and destroy crop residue after harvest.",
        "keywords": ["bollworm", "boll", "rosette", "pink larva"],
    },
    {
        "crop": "Cotton",
        "name": "Cotton leaf curl",
        "type": "Viral",
        "symptoms": ["Upward curling leaves", "Thickened veins", "Stunted plants and fewer bolls"],
        "remedy": "Remove infected plants and control whitefly. Virus-infected plants cannot be cured.",
        "prevention": "Use resistant varieties, manage whitefly early and avoid planting near infected fields.",
        "keywords": ["leaf curl", "curling", "whitefly", "vein"],
    },
    {
        "crop": "Onion",
        "name": "Purple blotch",
        "type": "Fungal",
        "symptoms": ["Purple-brown leaf lesions", "White centres with dark borders", "Leaf tip drying"],
        "remedy": "Spray Mancozeb with Carbendazim at label dose; repeat after 10-12 days in humid weather.",
        "prevention": "Crop rotation, wider spacing, drip irrigation and removal of infected foliage.",
        "keywords": ["purple", "blotch", "lesion", "leaf tip"],
    },
    {
        "crop": "Onion",
        "name": "Thrips",
        "type": "Pest",
        "symptoms": ["Silver-white streaks on leaves", "Curled leaf tips", "Tiny insects in leaf folds"],
        "remedy": "Use blue sticky traps and Fipronil 5% SC at label dose; spray in the evening to protect pollinators.",
        "prevention": "Avoid excess nitrogen, keep weeds low and rotate insecticides to prevent resistance.",
        "keywords": ["thrips", "silver", "curl", "tiny insect"],
    },
    {
        "crop": "Tomato",
        "name": "Late blight",
        "type": "Fungal",
        "symptoms": ["Dark water-soaked leaf patches", "White fungal growth under leaves", "Brown firm fruit rot"],
        "remedy": "Spray Metalaxyl with Mancozeb at label dose and remove infected plants. Avoid overhead irrigation.",
        "prevention": "Use certified seed, stake plants for airflow and avoid working in wet fields.",
        "keywords": ["late blight", "water-soaked", "white growth", "fruit rot"],
    },
    {
        "crop": "Tomato",
        "name": "Tomato leaf curl",
        "type": "Viral",
        "symptoms": ["Upward curling leaves", "Yellowing between veins", "Stunted plants and small fruit"],
        "remedy": "Remove infected plants and manage whitefly with recommended sprays. No chemical cures the virus.",
        "prevention": "Use resistant hybrids, insect-proof nursery trays and yellow sticky traps.",
        "keywords": ["leaf curl", "curl", "whitefly", "yellowing", "stunted"],
    },
    {
        "crop": "Potato",
        "name": "Late blight",
        "type": "Fungal",
        "symptoms": ["Dark water-soaked leaf patches", "White fuzzy growth on leaf undersides", "Rotting tubers"],
        "remedy": "Spray Mancozeb or Cymoxanil + Mancozeb at label dose; destroy infected haulms and stop moving infected seed.",
        "prevention": "Use certified seed, earthing up and avoid overhead irrigation in cool, humid weather.",
        "keywords": ["late blight", "water-soaked", "white growth", "rot"],
    },
    {
        "crop": "Potato",
        "name": "Common scab",
        "type": "Bacterial",
        "symptoms": ["Corky brown scab spots on tubers", "Rough patches on skin", "Reduced market grade"],
        "remedy": "Keep soil moisture even during tuber formation and avoid fresh manure or lime before planting.",
        "prevention": "Use certified seed, crop rotation and avoid potato after potato.",
        "keywords": ["scab", "corky", "tuber", "spots"],
    },
    {
        "crop": "Banana",
        "name": "Panama wilt",
        "type": "Fungal",
        "symptoms": ["Yellowing of older leaves", "Pseudostem splitting", "Wilting and plant collapse"],
        "remedy": "Remove and destroy infected plants. Apply Trichoderma-enriched compost and avoid replanting in the same pit.",
        "prevention": "Use tissue-culture planting material, resistant varieties and clean farm tools.",
        "keywords": ["wilt", "panama", "yellow leaf", "splitting"],
    },
    {
        "crop": "Banana",
        "name": "Sigatoka leaf spot",
        "type": "Fungal",
        "symptoms": ["Yellow-brown streaks on leaves", "Dark spots with grey centres", "Early leaf drying"],
        "remedy": "Remove infected leaves and spray Propiconazole or Mancozeb at label dose during humid spells.",
        "prevention": "Maintain plant spacing, remove de-leafed material and avoid overcrowded blocks.",
        "keywords": ["leaf spot", "sigatoka", "streak", "spot"],
    },
    {
        "crop": "Mango",
        "name": "Anthracnose",
        "type": "Fungal",
        "symptoms": ["Black sunken spots on fruit", "Blossom blight", "Brown lesions on leaves"],
        "remedy": "Spray Carbendazim or Mancozeb at recommended stages and follow with hot-water treatment of harvested fruit.",
        "prevention": "Prune for airflow, remove fallen leaves and avoid overhead irrigation during flowering.",
        "keywords": ["anthracnose", "black spot", "fruit", "blossom"],
    },
    {
        "crop": "Mango",
        "name": "Mango hopper",
        "type": "Pest",
        "symptoms": ["Small green-brown insects on shoots", "Sticky honeydew and sooty mould", "Flowers and young fruit drop"],
        "remedy": "Prune dense canopy and use Imidacloprid or recommended neem formulation at label dose during early infestation.",
        "prevention": "Avoid excess nitrogen, keep weeds down and monitor new shoots.",
        "keywords": ["hopper", "sooty", "honeydew", "insect"],
    },
    {
        "crop": "Apple",
        "name": "Apple scab",
        "type": "Fungal",
        "symptoms": ["Olive-green velvety spots", "Black spots on fruit", "Leaf yellowing and fall"],
        "remedy": "Spray Captan or Dodine at recommended stages from green tip; repeat during wet weather as per label.",
        "prevention": "Collect and destroy fallen leaves, prune for airflow and grow scab-tolerant varieties.",
        "keywords": ["scab", "olive", "velvet", "black spot"],
    },
    {
        "crop": "Apple",
        "name": "Powdery mildew",
        "type": "Fungal",
        "symptoms": ["White powdery coating on shoots", "Curled young leaves", "Poor fruit set"],
        "remedy": "Spray wettable sulphur at label dose and remove heavily infected shoots.",
        "prevention": "Avoid excess nitrogen, prune for light and airflow and keep the orchard clean.",
        "keywords": ["powder", "white", "mildew", "curl"],
    },
    {
        "crop": "Grapes",
        "name": "Downy mildew",
        "type": "Fungal",
        "symptoms": ["Yellow oil spots on upper leaves", "White downy growth underneath", "Brown shrivelled berries"],
        "remedy": "Spray Metalaxyl + Mancozeb at label dose, remove infected shoots and improve canopy ventilation.",
        "prevention": "Train vines for airflow, avoid evening irrigation and monitor humidity.",
        "keywords": ["downy", "oil spot", "white down", "berry"],
    },
    {
        "crop": "Grapes",
        "name": "Powdery mildew",
        "type": "Fungal",
        "symptoms": ["White ash-like powder on berries", "Cracked or russeted fruit", "Weak shoots"],
        "remedy": "Use sulphur-based sprays at recommended stages and maintain open canopy.",
        "prevention": "Prune for airflow, avoid dense foliage and follow a preventive spray calendar.",
        "keywords": ["powder", "white", "mildew", "berry"],
    },
    {
        "crop": "Orange",
        "name": "Citrus greening (HLB)",
        "type": "Bacterial",
        "symptoms": ["Mottled yellow leaves", "Lopsided bitter fruit", "Slow decline of the tree"],
        "remedy": "Remove and destroy infected trees. Manage the citrus psyllid vector and use certified saplings.",
        "prevention": "Buy from certified nurseries, control psyllids early and avoid moving infected material.",
        "keywords": ["greening", "hlb", "mottled", "lopsided"],
    },
    {
        "crop": "Orange",
        "name": "Citrus canker",
        "type": "Bacterial",
        "symptoms": ["Raised corky brown lesions", "Yellow halo around spots", "Leaf and fruit blemishes"],
        "remedy": "Spray copper oxychloride at label dose and prune out heavily infected twigs.",
        "prevention": "Use disease-free saplings, windbreaks and disinfected pruning tools.",
        "keywords": ["canker", "corky", "lesion", "halo"],
    },
    {
        "crop": "Tomato",
        "name": "Early blight",
        "type": "Fungal",
        "symptoms": ["Brown spots with concentric rings", "Lower leaves yellow and drop", "Sunken stem lesions near soil"],
        "remedy": "Remove affected lower leaves and spray Mancozeb 75% WP at 2 g/litre at label dose; repeat after 7-10 days if the weather stays humid.",
        "prevention": "Rotate away from tomato and potato, stake plants for airflow and avoid overhead irrigation.",
        "keywords": ["early blight", "target spot", "concentric", "lower leaf"],
    },
    {
        "crop": "Tomato",
        "name": "Septoria leaf spot",
        "type": "Fungal",
        "symptoms": ["Small grey spots with dark borders", "Tiny black dots inside spots", "Lower leaves dry and fall"],
        "remedy": "Remove infected leaves and spray Mancozeb or chlorothalonil at label dose; keep foliage dry.",
        "prevention": "Mulch to stop soil splash, rotate crops and clean stakes and tools between seasons.",
        "keywords": ["septoria", "grey spot", "black dot", "lower leaf"],
    },
    {
        "crop": "Tomato",
        "name": "Leaf mold",
        "type": "Fungal",
        "symptoms": ["Pale yellow patches on upper leaves", "Olive-green fuzzy mould underneath", "Leaves curl and drop"],
        "remedy": "Improve ventilation, avoid leaf wetness and use a labelled fungicide such as chlorothalonil if it keeps spreading.",
        "prevention": "Keep humidity down in polyhouses, prune lower leaves and space plants.",
        "keywords": ["leaf mold", "mould", "fuzzy", "yellow patch"],
    },
    {
        "crop": "Tomato",
        "name": "Bacterial spot",
        "type": "Bacterial",
        "symptoms": ["Small dark water-soaked spots", "Spots with yellow halos", "Scabby spots on fruit"],
        "remedy": "Remove infected debris and spray copper oxychloride at label dose; do not work in wet foliage.",
        "prevention": "Use clean seed, rotate crops and avoid overhead irrigation.",
        "keywords": ["bacterial spot", "halo", "scab", "water-soaked"],
    },
    {
        "crop": "Tomato",
        "name": "Spider mites",
        "type": "Pest",
        "symptoms": ["Fine webbing under leaves", "Tiny pale speckles on leaves", "Leaves turn yellow and dry"],
        "remedy": "Spray water under the leaves, then use a labelled acaricide or neem-based spray; repeat to break the life cycle.",
        "prevention": "Keep plants watered, avoid dusty dry spots and check leaf undersides every week.",
        "keywords": ["spider mite", "webbing", "speckle", "mite"],
    },
    {
        "crop": "Tomato",
        "name": "Target spot",
        "type": "Fungal",
        "symptoms": ["Brown spots with concentric rings", "Yellow halo around lesions", "Spots on leaves and fruit"],
        "remedy": "Remove infected leaves and spray Mancozeb or chlorothalonil at label dose; repeat in humid weather.",
        "prevention": "Wider spacing, drip irrigation and crop rotation.",
        "keywords": ["target spot", "concentric", "ring", "halo"],
    },
    {
        "crop": "Tomato",
        "name": "Tomato mosaic virus",
        "type": "Viral",
        "symptoms": ["Light and dark green mottling", "Distorted fern-like leaves", "Stunted growth"],
        "remedy": "Remove and destroy infected plants. The virus has no cure; control aphids and disinfect tools.",
        "prevention": "Use virus-free seed and resistant varieties, and wash hands before handling plants.",
        "keywords": ["mosaic", "mottle", "distorted", "virus"],
    },
    {
        "crop": "Potato",
        "name": "Early blight",
        "type": "Fungal",
        "symptoms": ["Dark brown target-like spots", "Yellowing between veins", "Lower leaves dry first"],
        "remedy": "Spray Mancozeb 75% WP at 2 g/litre at the first spots; repeat after 7-10 days as per label.",
        "prevention": "Rotate crops, keep plants well fed and avoid overhead irrigation.",
        "keywords": ["early blight", "target", "concentric", "lower leaf"],
    },
    {
        "crop": "Maize",
        "name": "Common rust",
        "type": "Fungal",
        "symptoms": ["Cinnamon-brown pustules on leaves", "Powder rubs off on fingers", "Yellowing around pustules"],
        "remedy": "Spray Propiconazole 25% EC at 1 ml/litre when pustules appear; follow label directions.",
        "prevention": "Grow resistant hybrids, sow on time and avoid excess nitrogen.",
        "keywords": ["common rust", "cinnamon", "pustule", "orange powder"],
    },
    {
        "crop": "Maize",
        "name": "Northern leaf blight",
        "type": "Fungal",
        "symptoms": ["Long grey-green lesions", "Lesions turn tan and papery", "Lower leaves blight first"],
        "remedy": "Spray Mancozeb 75% WP at 2 g/litre at the first lesions; repeat after 10-15 days in humid weather.",
        "prevention": "Resistant hybrids, crop rotation and residue management.",
        "keywords": ["northern leaf blight", "long lesion", "tan", "blight"],
    },
    {
        "crop": "Maize",
        "name": "Gray leaf spot",
        "type": "Fungal",
        "symptoms": ["Long rectangular grey lesions", "Lesions run between veins", "Heavy blighting in humid weather"],
        "remedy": "Spray azoxystrobin or mancozeb at label dose when lesions appear; follow label directions.",
        "prevention": "Rotate crops, manage residue and grow tolerant hybrids.",
        "keywords": ["gray leaf spot", "grey", "rectangular", "vein"],
    },
    {
        "crop": "Apple",
        "name": "Black rot",
        "type": "Fungal",
        "symptoms": ["Brown rot on fruit", "Concentric rings on fruit spots", "Purple leaf spots"],
        "remedy": "Prune out cankers and mummified fruit, and spray Captan at labelled stages.",
        "prevention": "Remove fallen fruit and dead wood, and keep the canopy open.",
        "keywords": ["black rot", "fruit rot", "mummy", "canker"],
    },
    {
        "crop": "Apple",
        "name": "Cedar apple rust",
        "type": "Fungal",
        "symptoms": ["Bright yellow-orange spots on leaves", "Rusty spores underneath", "Deformed fruit"],
        "remedy": "Spray a labelled rust fungicide such as myclobutanil from bud break, following label directions.",
        "prevention": "Remove nearby juniper or cedar hosts where practical and grow tolerant varieties.",
        "keywords": ["cedar", "rust", "orange spot", "juniper"],
    },
    {
        "crop": "Grapes",
        "name": "Black rot",
        "type": "Fungal",
        "symptoms": ["Brown leaf spots with dark borders", "Shrivelled black berries", "Black fruiting dots on fruit"],
        "remedy": "Remove mummified berries and spray Mancozeb or myclobutanil at labelled growth stages.",
        "prevention": "Open the canopy, remove debris and follow a preventive spray calendar.",
        "keywords": ["black rot", "mummified", "berry", "black dot"],
    },
    {
        "crop": "Grapes",
        "name": "Esca (black measles)",
        "type": "Fungal",
        "symptoms": ["Yellow-brown tiger-stripe leaves", "Dark streaks in wood", "Sudden vine decline"],
        "remedy": "Prune out affected wood in dry weather and remove severely declining vines; there is no reliable chemical cure.",
        "prevention": "Use clean planting material, disinfect pruning tools and avoid large pruning wounds.",
        "keywords": ["esca", "tiger", "measles", "wood"],
    },
    {
        "crop": "Grapes",
        "name": "Isariopsis leaf spot",
        "type": "Fungal",
        "symptoms": ["Angular brown spots between veins", "Olive-grey mould underneath", "Premature leaf drop"],
        "remedy": "Remove infected leaves and spray Mancozeb at label dose during humid weather.",
        "prevention": "Improve airflow, avoid overhead irrigation and keep the vineyard clean.",
        "keywords": ["isariopsis", "angular", "olive", "leaf spot"],
    },
]


def schemes_for_crop(crop: str | None, category: str | None = None) -> list[dict]:
    specific, generic = [], []
    for scheme in SCHEMES:
        tags = scheme["tags"]
        if crop and (crop in tags or (category and category in tags)):
            specific.append(scheme)
        elif "All" in tags:
            generic.append(scheme)
    return specific + generic


def diseases_for_crop(crop: str) -> list[dict]:
    return [d for d in DISEASES if d["crop"] == crop]


def symptom_options(crop: str) -> list[str]:
    options: list[str] = []
    for disease in diseases_for_crop(crop):
        for symptom in disease["symptoms"]:
            if symptom not in options:
                options.append(symptom)
    return options


def match_diseases(crop: str, selected: list[str], limit: int = 2) -> list[tuple[dict, float]]:
    selected_set = {s.lower() for s in selected}
    scored = []
    for disease in diseases_for_crop(crop):
        symptoms = {s.lower() for s in disease["symptoms"]}
        overlap = len(symptoms & selected_set)
        score = overlap / max(1, len(symptoms))
        scored.append((disease, score))
    scored.sort(key=lambda item: item[1], reverse=True)
    return scored[:limit]


def find_diseases_by_text(crop: str, text: str, limit: int = 2) -> list[dict]:
    text = text.lower()
    ranked = []
    for disease in diseases_for_crop(crop):
        hits = sum(1 for kw in disease["keywords"] if kw in text)
        hits += sum(1 for s in disease["symptoms"] if s.lower() in text)
        ranked.append((disease, hits))
    ranked.sort(key=lambda item: item[1], reverse=True)
    matches = [d for d, hits in ranked if hits > 0]
    return (matches or [d for d, _ in ranked])[:limit]
