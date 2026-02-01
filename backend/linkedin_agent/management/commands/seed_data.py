"""Seed database with default templates and demo user."""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from linkedin_agent.api.models import PostTemplate, APIConfiguration


SYSTEM_TEMPLATES = [
    {
        "name": "Professional Insight",
        "description": "Share a professional insight with structured sections",
        "tone": "professional",
        "category": "tech",
        "structure_prompt": (
            "Structure the post with: Hook question or bold statement, "
            "Key Insights (2-3 points), Lessons Learned, Actionable Tips, "
            "Takeaway, Conclusion with CTA. Use short paragraphs."
        ),
        "example_post": "",
    },
    {
        "name": "Storytelling",
        "description": "Tell a compelling story with a lesson",
        "tone": "storytelling",
        "category": "career",
        "structure_prompt": (
            "Structure as a narrative: Start with a vivid scene or moment, "
            "Build the challenge/conflict, Share the turning point, "
            "Reveal the lesson/insight, End with a reflective question. "
            "Use first person, short sentences for impact."
        ),
        "example_post": "",
    },
    {
        "name": "Hot Take",
        "description": "Share a controversial or contrarian opinion",
        "tone": "controversial",
        "category": "tech",
        "structure_prompt": (
            "Start with a bold, contrarian statement. Present your argument "
            "with evidence. Acknowledge the other side briefly. Double down "
            "on your position. End with a provocative question. "
            "Keep paragraphs to 1-2 sentences max."
        ),
        "example_post": "",
    },
    {
        "name": "How-To Guide",
        "description": "Step-by-step educational content",
        "tone": "educational",
        "category": "productivity",
        "structure_prompt": (
            "Structure as: Problem statement, Why this matters, "
            "Step-by-step solution (numbered), Pro tips, "
            "Summary of key takeaways. Use bullet points and numbers."
        ),
        "example_post": "",
    },
    {
        "name": "Listicle",
        "description": "Numbered list of tips, tools, or insights",
        "tone": "casual",
        "category": "productivity",
        "structure_prompt": (
            "Start with a hook about why this list matters. "
            "Present 5-7 items, each with a brief explanation. "
            "Use emoji numbers or bullet points. End with a bonus tip "
            "and invitation to add to the list."
        ),
        "example_post": "",
    },
    {
        "name": "Leadership Reflection",
        "description": "Share leadership lessons and team insights",
        "tone": "inspirational",
        "category": "leadership",
        "structure_prompt": (
            "Start with a leadership challenge or moment. Share what you "
            "observed or learned. Connect to broader leadership principles. "
            "Offer advice for other leaders. End with an inspiring takeaway."
        ),
        "example_post": "",
    },
    {
        "name": "AI/ML Breakdown",
        "description": "Explain AI/ML concepts in accessible terms",
        "tone": "educational",
        "category": "ai_ml",
        "structure_prompt": (
            "Start with why this AI concept matters now. Explain it simply "
            "(ELI5 if possible). Show a real-world application. Discuss "
            "implications for professionals. End with what to watch for next."
        ),
        "example_post": "",
    },
    {
        "name": "Startup Lesson",
        "description": "Share startup or entrepreneurship experience",
        "tone": "storytelling",
        "category": "startup",
        "structure_prompt": (
            "Start with a specific startup moment (failure or success). "
            "Share the context briefly. Reveal what happened. Extract 2-3 "
            "clear lessons. End with advice for founders."
        ),
        "example_post": "",
    },
]


class Command(BaseCommand):
    help = "Seed database with default templates and demo user"

    def handle(self, *args, **options):
        # Create system templates
        created = 0
        for tmpl in SYSTEM_TEMPLATES:
            _, is_new = PostTemplate.objects.get_or_create(
                name=tmpl["name"],
                is_system=True,
                defaults=tmpl,
            )
            if is_new:
                created += 1

        self.stdout.write(f"Templates: {created} created, {len(SYSTEM_TEMPLATES) - created} already exist")

        # Create demo user
        if not User.objects.filter(username="demo").exists():
            user = User.objects.create_user(
                username="demo",
                email="demo@example.com",
                password="demo1234",
                first_name="Demo",
                last_name="User",
            )
            APIConfiguration.objects.create(user=user)
            self.stdout.write("Demo user created (demo / demo1234)")
        else:
            self.stdout.write("Demo user already exists")
