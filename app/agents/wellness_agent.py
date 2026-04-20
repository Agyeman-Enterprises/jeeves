"""
WellnessAgent — JARVIS fitness, nutrition, and meal planning specialist.
Personalized for Akua Agyeman: 60yo postmenopausal, losing 50kg over 12 months,
no pasta / fake meat / tofu / soy protein, smoothies for breakfast, 30-min meals.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

from app.agents.base import AgentContext, AgentResponse, BaseAgent

LOGGER = logging.getLogger(__name__)

# ── User profile constants ────────────────────────────────────────────────────
USER_PROFILE: Dict[str, Any] = {
    "age": 60,
    "stage": "postmenopausal",
    "fitness_level": "unfit",
    "weight_goal_kg": 50,          # total kg to lose
    "timeframe_months": 12,
    "diet_restrictions": ["no pasta", "no fake meat", "no tofu", "no soy protein"],
    "preferences": ["smoothies for breakfast", "quick meals 30min or less"],
}

# ── Exercise plan (hardcoded base plan, phased by month) ──────────────────────
EXERCISE_PLAN: Dict[str, Any] = {
    "notes": [
        "Weight-bearing exercise is critical for bone density postmenopause.",
        "Muscle mass preservation is the #1 metabolic priority — muscle burns fat at rest.",
        "Target 1g of protein per kg of goal body weight (50g/day minimum).",
        "6 days per week — rest day is non-negotiable for recovery.",
        "Stop immediately if you feel pain (not discomfort). Pain is not progress.",
    ],
    "phases": {
        "phase_1": {
            "label": "Phase 1 — Foundation",
            "months": "Months 1–2",
            "frequency": "6 days/week",
            "duration_min": 15,
            "routine": [
                {"exercise": "March in place", "duration": "2 min", "notes": "Warm up — swing arms, lift knees gently"},
                {"exercise": "Chair squats", "duration": "2 min", "sets_reps": "3 × 8", "notes": "Sit back onto chair, stand fully — controlled"},
                {"exercise": "Wall push-ups", "duration": "2 min", "sets_reps": "3 × 8", "notes": "Hands on wall at shoulder height — elbows out 45°"},
                {"exercise": "Side step-touch", "duration": "2 min", "notes": "Low-impact cardio — step right, touch, step left, touch"},
                {"exercise": "Seated leg lifts", "duration": "2 min", "sets_reps": "3 × 10 each leg", "notes": "Core + hip flexors — sit tall, lift straight leg"},
                {"exercise": "Standing hip circles + shoulder rolls", "duration": "2 min", "notes": "Mobility — 10 circles each direction, 10 shoulder rolls"},
                {"exercise": "Deep breathing cool down", "duration": "1 min", "notes": "4 counts in, 6 counts out — parasympathetic reset"},
            ],
        },
        "phase_2": {
            "label": "Phase 2 — Build",
            "months": "Months 3–4",
            "frequency": "6 days/week",
            "duration_min": 15,
            "upgrades_from_phase_1": [
                "Chair squats → full squats (no chair, full depth)",
                "Wall push-ups → incline push-ups on kitchen counter",
                "Add resistance band rows — 2 sets of 10",
                "Add balance drill: stand on one foot 30s each side",
            ],
            "routine": [
                {"exercise": "March in place", "duration": "2 min", "notes": "Warm up"},
                {"exercise": "Full squats", "duration": "2 min", "sets_reps": "3 × 8", "notes": "No chair — arms forward for counterbalance"},
                {"exercise": "Incline push-ups (counter)", "duration": "2 min", "sets_reps": "3 × 8", "notes": "Hands on kitchen counter — more load than wall"},
                {"exercise": "Resistance band rows", "duration": "2 min", "sets_reps": "2 × 10", "notes": "Band around door handle — pull elbows back"},
                {"exercise": "Side step-touch", "duration": "2 min", "notes": "Low-impact cardio"},
                {"exercise": "Balance drill — single leg stand", "duration": "2 min", "notes": "30s each side, twice. Use wall for support if needed"},
                {"exercise": "Deep breathing cool down", "duration": "1 min"},
            ],
        },
        "phase_3": {
            "label": "Phase 3 — Sustain",
            "months": "Month 5 onwards",
            "frequency": "6 days/week",
            "duration_min": 20,
            "upgrades_from_phase_2": [
                "Add light 1–2kg dumbbells to squats",
                "Add shoulder press with 1–2kg dumbbells (2 × 10)",
                "Extend session by 5 min brisk walk (outdoors or treadmill)",
            ],
            "routine": [
                {"exercise": "March in place", "duration": "2 min", "notes": "Warm up"},
                {"exercise": "Squats with dumbbells (1–2kg)", "duration": "2 min", "sets_reps": "3 × 10", "notes": "Hold dumbbells at sides"},
                {"exercise": "Incline push-ups", "duration": "2 min", "sets_reps": "3 × 10"},
                {"exercise": "Dumbbell shoulder press", "duration": "2 min", "sets_reps": "2 × 10", "notes": "Seated or standing — press overhead from ear level"},
                {"exercise": "Resistance band rows", "duration": "2 min", "sets_reps": "3 × 10"},
                {"exercise": "Balance drill + side step-touch combo", "duration": "2 min"},
                {"exercise": "Brisk walk", "duration": "5 min", "notes": "Outdoors preferred — sunlight for vitamin D"},
                {"exercise": "Deep breathing cool down", "duration": "1 min"},
            ],
        },
    },
}

# ── 7-day meal plan ───────────────────────────────────────────────────────────
MEAL_PLAN: Dict[str, Any] = {
    "overview": (
        "7-day rotation. Smoothies every morning (5 min). "
        "Lunch and dinner are interchangeable — all 30 min or under. "
        "No pasta, no fake meat, no tofu, no soy protein."
    ),
    "protein_target_g": 50,
    "days": {
        "monday": {
            "breakfast": {
                "meal": "Frozen berry + banana smoothie",
                "time_min": 5,
                "ingredients": ["frozen mixed berries", "1 banana", "large handful spinach",
                                "300ml unsweetened almond milk", "1 scoop protein powder (whey/pea)"],
                "notes": "Spinach is invisible in taste but packs iron and folate.",
            },
            "lunch": {
                "meal": "Baked salmon + steamed broccoli + quinoa",
                "time_min": 25,
                "ingredients": ["150g salmon fillet", "200g broccoli", "60g dry quinoa",
                                "olive oil", "lemon", "garlic", "salt", "pepper"],
                "notes": "Omega-3s from salmon support joint health and reduce inflammation postmenopause.",
            },
        },
        "tuesday": {
            "breakfast": {
                "meal": "Mango + ginger + turmeric smoothie",
                "time_min": 5,
                "ingredients": ["1 cup frozen mango", "1 tsp fresh grated ginger",
                                "½ tsp turmeric", "300ml coconut milk", "1 tbsp chia seeds"],
                "notes": "Turmeric + ginger are anti-inflammatory. Chia seeds add omega-3 and fibre.",
            },
            "lunch": {
                "meal": "Chicken + vegetable stir-fry + brown rice",
                "time_min": 20,
                "ingredients": ["150g chicken breast", "1 capsicum", "handful snap peas",
                                "1 carrot", "2 tbsp soy-free stir-fry sauce (coconut aminos)",
                                "sesame oil", "60g dry brown rice"],
                "notes": "Use coconut aminos instead of soy sauce — same flavour, no soy.",
            },
        },
        "wednesday": {
            "breakfast": {
                "meal": "Blueberry + oat + almond butter smoothie",
                "time_min": 5,
                "ingredients": ["1 cup frozen blueberries", "2 tbsp rolled oats", "1 tbsp flaxseed",
                                "1 tbsp almond butter", "300ml milk (dairy or almond)"],
                "notes": "Flaxseed provides lignans which help balance oestrogen postmenopause.",
            },
            "lunch": {
                "meal": "Grilled chicken + Greek salad with halloumi",
                "time_min": 15,
                "ingredients": ["150g chicken breast", "80g halloumi", "1 cucumber",
                                "2 tomatoes", "handful kalamata olives", "50g feta",
                                "olive oil", "lemon", "dried oregano"],
                "notes": "Halloumi + feta give extra calcium — critical for bone density.",
            },
        },
        "thursday": {
            "breakfast": {
                "meal": "Pineapple + cucumber + mint cooler smoothie",
                "time_min": 5,
                "ingredients": ["1 cup frozen pineapple", "½ cucumber", "handful fresh mint",
                                "juice of 1 lime", "300ml coconut water"],
                "notes": "Hydrating and digestive. Coconut water replenishes electrolytes.",
            },
            "lunch": {
                "meal": "Prawn + cauliflower egg-fried rice",
                "time_min": 20,
                "ingredients": ["150g raw prawns", "1 head cauliflower (riced)", "2 eggs",
                                "½ cup frozen peas", "2 spring onions", "coconut aminos",
                                "sesame oil", "garlic", "ginger"],
                "notes": "Cauliflower rice = all the satisfaction of fried rice at a fraction of the carbs.",
            },
        },
        "friday": {
            "breakfast": {
                "meal": "Strawberry + avocado + cacao smoothie",
                "time_min": 5,
                "ingredients": ["1 cup frozen strawberries", "½ avocado", "1 tbsp cacao powder",
                                "300ml unsweetened almond milk", "1 tsp honey (optional)"],
                "notes": "Healthy fats from avocado support hormone production and skin health.",
            },
            "lunch": {
                "meal": "Turkey mince lettuce cups + avocado salsa",
                "time_min": 20,
                "ingredients": ["200g turkey mince", "iceberg lettuce leaves", "1 avocado",
                                "1 tomato", "½ red onion", "lime juice", "coriander",
                                "garlic", "cumin", "smoked paprika"],
                "notes": "Turkey is high in tryptophan, which supports serotonin — mood matters postmenopause.",
            },
        },
        "saturday": {
            "breakfast": {
                "meal": "Kale + apple + ginger green smoothie",
                "time_min": 5,
                "ingredients": ["2 large kale leaves (stems removed)", "1 green apple",
                                "1 tsp fresh ginger", "juice of ½ lemon", "300ml water or coconut water"],
                "notes": "Pure detox green. Use cold water for a less intense flavour.",
            },
            "lunch": {
                "meal": "Tuna nicoise salad",
                "time_min": 15,
                "ingredients": ["1 can tuna in olive oil", "2 eggs (hard-boiled)", "handful green beans (blanched)",
                                "2 small potatoes (boiled)", "handful kalamata olives",
                                "cherry tomatoes", "Dijon mustard dressing"],
                "notes": "Eggs + tuna = protein + B12 + vitamin D combo. Keep potatoes small — just enough for energy.",
            },
        },
        "sunday": {
            "breakfast": {
                "meal": "Beetroot + mixed berry + banana smoothie",
                "time_min": 5,
                "ingredients": ["½ cup cooked beetroot (vacuum packed)", "1 cup frozen mixed berries",
                                "1 banana", "200g Greek yogurt", "splash of water to blend"],
                "notes": "Greek yogurt gives 15-20g protein in one hit. Beetroot boosts circulation and stamina.",
            },
            "lunch": {
                "meal": "Roast chicken thighs + roasted root vegetables",
                "time_min": 30,
                "ingredients": ["4 bone-in chicken thighs (skin on)", "2 carrots", "2 parsnips",
                                "1 sweet potato", "1 red onion", "olive oil", "rosemary",
                                "thyme", "garlic", "salt", "pepper"],
                "notes": "Sunday cook — make double. Cold chicken thighs work perfectly in Monday salads.",
            },
        },
    },
}

# ── Weekly shopping list (grouped by category) ────────────────────────────────
SHOPPING_LIST: Dict[str, List[str]] = {
    "Proteins — Meat & Fish": [
        "Salmon fillets × 2 (approx 300g total)",
        "Chicken breast × 2 (approx 300g total)",
        "Chicken thighs, bone-in skin-on × 4",
        "Turkey mince 200g",
        "Raw prawns 150g (fresh or frozen)",
        "Tuna in olive oil × 2 cans",
    ],
    "Proteins — Dairy & Eggs": [
        "Greek yogurt 500g (full-fat, plain)",
        "Halloumi 1 pack (approx 225g)",
        "Feta cheese 200g",
        "Eggs × 6",
        "Milk (dairy or almond) 1L",
        "Whey or pea protein powder (1 scoop per day — ensure no soy isolate)",
    ],
    "Fresh Vegetables": [
        "Broccoli 1 large head",
        "Cauliflower 1 head",
        "Kale 1 bunch",
        "Spinach 1 bag",
        "Snap peas 1 bag",
        "Capsicum (red or mixed) × 2",
        "Carrots × 4",
        "Cucumber × 2",
        "Iceberg lettuce 1 head",
        "Spring onions 1 bunch",
        "Cherry tomatoes 1 punnet",
        "Tomatoes × 4",
        "Red onion × 2",
        "Parsnips × 2",
        "Sweet potato × 1",
        "Green beans 1 bag (or frozen)",
        "Baby potatoes 300g (small)",
    ],
    "Fresh Fruit": [
        "Bananas × 3",
        "Green apple × 1",
        "Lime × 2",
        "Lemon × 2",
        "Avocado × 3 (buy 2 ripe + 1 firm for later in week)",
        "Beetroot, vacuum-packed cooked × 1 pack",
    ],
    "Frozen Fruit & Veg": [
        "Frozen mixed berries 500g",
        "Frozen blueberries 300g",
        "Frozen strawberries 300g",
        "Frozen mango chunks 300g",
        "Frozen pineapple chunks 300g",
        "Frozen peas 1 bag",
    ],
    "Pantry — Grains & Staples": [
        "Quinoa 500g",
        "Brown rice 500g",
        "Rolled oats 500g",
    ],
    "Pantry — Nuts, Seeds & Oils": [
        "Almond butter 1 jar",
        "Chia seeds",
        "Flaxseed (ground)",
        "Olive oil 500ml",
        "Sesame oil (small bottle)",
        "Coconut aminos (soy-free soy sauce substitute)",
    ],
    "Pantry — Spices & Condiments": [
        "Turmeric (ground)",
        "Ginger (fresh root × 1 + ground as backup)",
        "Garlic bulb × 1",
        "Cumin (ground)",
        "Smoked paprika",
        "Dried oregano",
        "Rosemary (fresh or dried)",
        "Thyme (fresh or dried)",
        "Dijon mustard",
        "Cacao powder",
        "Honey (small jar — optional)",
    ],
    "Canned & Jarred": [
        "Kalamata olives 1 jar",
        "Coconut milk 400ml × 2 cans",
    ],
    "Beverages": [
        "Coconut water 1L",
        "Unsweetened almond milk 2L (if not buying dairy)",
    ],
    "Refrigerated — Misc": [
        "Halloumi (already listed above under proteins — do not double-buy)",
    ],
}

# ── Intent keyword sets ───────────────────────────────────────────────────────
_EXERCISE_KEYWORDS = {
    "exercise", "workout", "fitness", "routine", "training", "cardio",
    "strength", "physical", "active", "gym", "walk", "squat", "push-up",
    "pushup", "phase", "month 1", "month 2", "month 3", "phase 1", "phase 2",
}
_MEAL_KEYWORDS = {
    "meal", "meal plan", "food plan", "eat", "eating", "recipe", "recipes",
    "smoothie", "breakfast", "lunch", "dinner", "weekly menu", "what to eat",
    "nutrition", "diet", "cook", "cooking",
}
_SHOPPING_KEYWORDS = {
    "shopping", "shopping list", "grocery", "groceries", "buy", "supermarket",
    "shop", "ingredients", "what to buy",
}
_SUPPORTS_KEYWORDS = _EXERCISE_KEYWORDS | _MEAL_KEYWORDS | _SHOPPING_KEYWORDS | {
    "weight loss", "lose weight", "healthy", "health", "wellness", "wellbeing",
    "fat loss", "calories", "protein", "carb", "fibre", "fiber", "supplement",
    "vitamin", "mineral", "postmenopause", "menopause",
}


def _detect_intent(query: str) -> str:
    """Classify the query into one of four intents."""
    q = query.lower()
    words = set(q.split())

    # Check for shopping list first (often combined with "meal")
    if _SHOPPING_KEYWORDS & words or any(kw in q for kw in _SHOPPING_KEYWORDS):
        return "shopping_list"

    if _EXERCISE_KEYWORDS & words or any(kw in q for kw in _EXERCISE_KEYWORDS):
        return "exercise_plan"

    if _MEAL_KEYWORDS & words or any(kw in q for kw in _MEAL_KEYWORDS):
        return "meal_plan"

    return "general_wellness"


def _format_exercise_plan() -> str:
    """Return a human-readable exercise plan."""
    lines: List[str] = [
        "15-Minute Daily Exercise Plan",
        f"Tailored for: {USER_PROFILE['age']}yo postmenopausal woman, beginner fitness level",
        f"Frequency: 6 days/week  |  Goal: -{USER_PROFILE['weight_goal_kg']}kg over {USER_PROFILE['timeframe_months']} months",
        "",
        "IMPORTANT NOTES:",
    ]
    for note in EXERCISE_PLAN["notes"]:
        lines.append(f"  • {note}")

    for phase_key, phase in EXERCISE_PLAN["phases"].items():
        lines.append("")
        lines.append(f"── {phase['label']} ({phase['months']}) ──")
        lines.append(f"   {phase['frequency']}  |  {phase['duration_min']} min/session")

        if "upgrades_from_phase_1" in phase:
            lines.append("   Upgrades from Phase 1:")
            for u in phase["upgrades_from_phase_1"]:
                lines.append(f"     → {u}")
        if "upgrades_from_phase_2" in phase:
            lines.append("   Upgrades from Phase 2:")
            for u in phase["upgrades_from_phase_2"]:
                lines.append(f"     → {u}")

        lines.append("   Routine:")
        for step in phase["routine"]:
            sets = f"  [{step['sets_reps']}]" if "sets_reps" in step else ""
            note = f"  — {step['notes']}" if step.get("notes") else ""
            lines.append(f"     {step['duration']:8}  {step['exercise']}{sets}{note}")

    return "\n".join(lines)


def _format_meal_plan() -> str:
    """Return a human-readable 7-day meal plan."""
    lines: List[str] = [
        "7-Day Meal Plan",
        MEAL_PLAN["overview"],
        f"Protein target: {MEAL_PLAN['protein_target_g']}g+ per day",
        "",
    ]
    for day, meals in MEAL_PLAN["days"].items():
        lines.append(f"── {day.upper()} ──")
        b = meals["breakfast"]
        lines.append(f"  Breakfast ({b['time_min']} min): {b['meal']}")
        lines.append(f"    {', '.join(b['ingredients'])}")
        if b.get("notes"):
            lines.append(f"    Note: {b['notes']}")
        l = meals["lunch"]
        lines.append(f"  Lunch/Dinner ({l['time_min']} min): {l['meal']}")
        lines.append(f"    {', '.join(l['ingredients'])}")
        if l.get("notes"):
            lines.append(f"    Note: {l['notes']}")
        lines.append("")
    return "\n".join(lines)


def _format_shopping_list() -> str:
    """Return a human-readable grouped shopping list."""
    lines: List[str] = [
        "Weekly Shopping List",
        "Based on the 7-day meal plan. All items for one person, one week.",
        "",
    ]
    for category, items in SHOPPING_LIST.items():
        if category == "Refrigerated — Misc":
            continue  # skip the duplicate note
        lines.append(f"[ {category} ]")
        for item in items:
            lines.append(f"  ☐ {item}")
        lines.append("")
    return "\n".join(lines)


# ── Optional LLM fallback ─────────────────────────────────────────────────────
try:
    import anthropic as _anthropic
    _ANTHROPIC_AVAILABLE = True
except ImportError:
    _anthropic = None  # type: ignore[assignment]
    _ANTHROPIC_AVAILABLE = False


def _call_claude(query: str) -> str:
    """
    Fall back to claude-haiku-4-5-20251001 for open-ended wellness questions
    that don't map to the structured plans.
    """
    if not _ANTHROPIC_AVAILABLE:
        return (
            "I can answer specific wellness questions, but the Anthropic package "
            "is not installed. Ask me about your exercise plan, meal plan, or shopping list."
        )

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return (
            "ANTHROPIC_API_KEY not set. "
            "I can still give you your exercise plan, meal plan, or shopping list — just ask."
        )

    try:
        client = _anthropic.Anthropic(api_key=api_key)
        system_prompt = (
            "You are a wellness specialist for a 60-year-old postmenopausal woman "
            "who wants to lose 50kg over 12 months. She is a beginner in fitness. "
            "Dietary restrictions: no pasta, no fake meat, no tofu, no soy protein. "
            "She prefers smoothies for breakfast and quick meals under 30 minutes. "
            "Give direct, practical, evidence-based advice. No filler, no fluff. "
            "Keep responses concise and actionable."
        )
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=600,
            system=system_prompt,
            messages=[{"role": "user", "content": query}],
        )
        return response.content[0].text  # type: ignore[index]
    except Exception as exc:
        LOGGER.warning("WellnessAgent LLM fallback failed: %s", exc)
        return (
            f"I couldn't reach the AI for that question ({exc}). "
            "Ask me about your exercise plan, meal plan, or shopping list."
        )


# ── Agent ─────────────────────────────────────────────────────────────────────
class WellnessAgent(BaseAgent):
    """
    Handles fitness, nutrition, meal planning, and shopping lists.
    Personalised for Akua: 60yo postmenopausal, beginner fitness, -50kg goal.
    """

    name = "WellnessAgent"
    description = (
        "Personal wellness specialist — exercise plans, meal plans, "
        "nutrition guidance, and weekly shopping lists. "
        "Tailored for postmenopausal women focused on fat loss and muscle preservation."
    )
    capabilities = [
        "Generate a phased 15-minute daily exercise plan",
        "Provide a 7-day meal plan (smoothies AM, 30-min meals)",
        "Generate a categorised weekly shopping list",
        "Answer general nutrition and wellness questions",
    ]

    def supports(self, query: str) -> bool:
        q = query.lower()
        return any(kw in q for kw in _SUPPORTS_KEYWORDS)

    def handle(self, query: str, context: Optional[AgentContext] = None) -> AgentResponse:
        intent = _detect_intent(query)
        LOGGER.debug("WellnessAgent intent=%s query=%r", intent, query[:80])

        if intent == "exercise_plan":
            return self._handle_exercise_plan()

        if intent == "meal_plan":
            return self._handle_meal_plan()

        if intent == "shopping_list":
            return self._handle_shopping_list()

        # general_wellness — fall back to Claude
        return self._handle_general_wellness(query)

    # ── Intent handlers ───────────────────────────────────────────────────────

    def _handle_exercise_plan(self) -> AgentResponse:
        content = _format_exercise_plan()
        return AgentResponse(
            agent=self.name,
            content=content,
            data={
                "intent": "exercise_plan",
                "user_profile": USER_PROFILE,
                "plan": EXERCISE_PLAN,
            },
        )

    def _handle_meal_plan(self) -> AgentResponse:
        content = _format_meal_plan()
        return AgentResponse(
            agent=self.name,
            content=content,
            data={
                "intent": "meal_plan",
                "user_profile": USER_PROFILE,
                "meal_plan": MEAL_PLAN,
            },
        )

    def _handle_shopping_list(self) -> AgentResponse:
        content = _format_shopping_list()
        return AgentResponse(
            agent=self.name,
            content=content,
            data={
                "intent": "shopping_list",
                "user_profile": USER_PROFILE,
                "shopping_list": SHOPPING_LIST,
            },
        )

    def _handle_general_wellness(self, query: str) -> AgentResponse:
        content = _call_claude(query)
        return AgentResponse(
            agent=self.name,
            content=content,
            data={
                "intent": "general_wellness",
                "user_profile": USER_PROFILE,
            },
        )
