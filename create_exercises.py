#!/usr/bin/env python
"""
Create all 100 exercises EX001-EX100 atomically
"""
from django.db import transaction

from apps.workouts.models import Exercise

# All 100 exercises from our prompts
EXERCISES = [
    ("EX001", "Push-ups", ["chest", "arms"]),
    ("EX002", "Squats", ["legs"]),
    ("EX003", "Pull-ups", ["back", "arms"]),
    ("EX004", "Lunges", ["legs"]),
    ("EX005", "Plank", ["core"]),
    ("EX006", "Deadlifts", ["back", "legs"]),
    ("EX007", "Bench Press", ["chest"]),
    ("EX008", "Rows", ["back"]),
    ("EX009", "Burpees", ["full_body"]),
    ("EX010", "Mountain Climbers", ["core"]),
    ("EX011", "Jumping Jacks", ["full_body"]),
    ("EX012", "Dips", ["chest", "arms"]),
    ("EX013", "Leg Raises", ["core"]),
    ("EX014", "Crunches", ["core"]),
    ("EX015", "Russian Twists", ["core"]),
    ("EX016", "Wall Sits", ["legs"]),
    ("EX017", "High Knees", ["legs"]),
    ("EX018", "Butt Kicks", ["legs"]),
    ("EX019", "Jump Rope", ["full_body"]),
    ("EX020", "Box Jumps", ["legs"]),
    ("EX021", "Step-ups", ["legs"]),
    ("EX022", "Lateral Raises", ["shoulders"]),
    ("EX023", "Bicep Curls", ["arms"]),
    ("EX024", "Tricep Extensions", ["arms"]),
    ("EX025", "Shoulder Press", ["shoulders"]),
    ("EX026", "Chest Flyes", ["chest"]),
    ("EX027", "Reverse Flyes", ["shoulders", "back"]),
    ("EX028", "Upright Rows", ["shoulders"]),
    ("EX029", "Shrugs", ["shoulders"]),
    ("EX030", "Face Pulls", ["shoulders", "back"]),
    ("EX031", "Hammer Curls", ["arms"]),
    ("EX032", "Concentration Curls", ["arms"]),
    ("EX033", "Preacher Curls", ["arms"]),
    ("EX034", "Cable Curls", ["arms"]),
    ("EX035", "Overhead Press", ["shoulders"]),
    ("EX036", "Arnold Press", ["shoulders"]),
    ("EX037", "Lateral Raises", ["shoulders"]),
    ("EX038", "Front Raises", ["shoulders"]),
    ("EX039", "Rear Delt Flyes", ["shoulders"]),
    ("EX040", "Pike Push-ups", ["shoulders", "arms"]),
    ("EX041", "Handstand Push-ups", ["shoulders", "arms"]),
    ("EX042", "Diamond Push-ups", ["chest", "arms"]),
    ("EX043", "Wide Push-ups", ["chest"]),
    ("EX044", "Decline Push-ups", ["chest", "arms"]),
    ("EX045", "Incline Push-ups", ["chest", "arms"]),
    ("EX046", "Hindu Push-ups", ["chest", "shoulders"]),
    ("EX047", "Archer Push-ups", ["chest", "arms"]),
    ("EX048", "One-arm Push-ups", ["chest", "arms"]),
    ("EX049", "Clap Push-ups", ["chest", "arms"]),
    ("EX050", "Bulgarian Split Squats", ["legs"]),
    ("EX051", "Goblet Squats", ["legs"]),
    ("EX052", "Jump Squats", ["legs"]),
    ("EX053", "Pistol Squats", ["legs"]),
    ("EX054", "Sumo Squats", ["legs"]),
    ("EX055", "Cossack Squats", ["legs"]),
    ("EX056", "Single Leg Deadlifts", ["legs", "back"]),
    ("EX057", "Romanian Deadlifts", ["legs", "back"]),
    ("EX058", "Stiff Leg Deadlifts", ["legs", "back"]),
    ("EX059", "Deficit Deadlifts", ["legs", "back"]),
    ("EX060", "Rack Pulls", ["back"]),
    ("EX061", "Good Mornings", ["back", "legs"]),
    ("EX062", "Hip Thrusts", ["legs"]),
    ("EX063", "Glute Bridges", ["legs"]),
    ("EX064", "Calf Raises", ["legs"]),
    ("EX065", "Single Leg Calf Raises", ["legs"]),
    ("EX066", "Seated Calf Raises", ["legs"]),
    ("EX067", "Leg Curls", ["legs"]),
    ("EX068", "Leg Extensions", ["legs"]),
    ("EX069", "Leg Press", ["legs"]),
    ("EX070", "Walking Lunges", ["legs"]),
    ("EX071", "Reverse Lunges", ["legs"]),
    ("EX072", "Side Lunges", ["legs"]),
    ("EX073", "Curtsy Lunges", ["legs"]),
    ("EX074", "Clock Lunges", ["legs"]),
    ("EX075", "Jump Lunges", ["legs"]),
    ("EX076", "Chest Press", ["chest"]),
    ("EX077", "Incline Press", ["chest"]),
    ("EX078", "Decline Press", ["chest"]),
    ("EX079", "Dumbbell Press", ["chest"]),
    ("EX080", "Dumbbell Flyes", ["chest"]),
    ("EX081", "Cable Crossovers", ["chest"]),
    ("EX082", "Pec Deck", ["chest"]),
    ("EX083", "T-Bar Rows", ["back"]),
    ("EX084", "Cable Rows", ["back"]),
    ("EX085", "Lat Pulldowns", ["back"]),
    ("EX086", "Wide Grip Pull-ups", ["back", "arms"]),
    ("EX087", "Chin-ups", ["back", "arms"]),
    ("EX088", "Inverted Rows", ["back"]),
    ("EX089", "Single Arm Rows", ["back"]),
    ("EX090", "Bent Over Rows", ["back"]),
    ("EX091", "Pendlay Rows", ["back"]),
    ("EX092", "Meadows Rows", ["back"]),
    ("EX093", "Seal Rows", ["back"]),
    ("EX094", "Chest Supported Rows", ["back"]),
    ("EX095", "Machine Rows", ["back"]),
    ("EX096", "Resistance Band Rows", ["back"]),
    ("EX097", "TRX Rows", ["back"]),
    ("EX098", "Landmine Rows", ["back"]),
    ("EX099", "Renegade Rows", ["back", "core"]),
    ("EX100", "Gorilla Rows", ["back"])
]

def create_exercises():
    created, skipped, errors = 0, 0, []
    
    try:
        with transaction.atomic():
            for code, name, muscle_groups in EXERCISES:
                obj, was_created = Exercise.objects.update_or_create(
                    id=code,
                    defaults={
                        'slug': code.lower(),  # ex001, ex002, etc.
                        'name': name,
                        'description': f'{name} - proper form and technique',
                        'difficulty': 'beginner',
                        'is_active': True
                    }
                )
                if was_created:
                    created += 1
                    print(f"✓ Created {code}: {name}")
                else:
                    skipped += 1
                    print(f"- Skipped {code}: {name} (already exists)")
                    
        print(f"\n✅ SUCCESS: {created} created, {skipped} skipped")
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        errors.append(str(e))
        return False

if __name__ == "__main__":
    print("🚀 Creating 100 exercises EX001-EX100...")
    print("=" * 50)
    
    success = create_exercises()
    
    print("=" * 50)
    print(f"Total exercises in database: {Exercise.objects.count()}")
    print(f"EX exercises: {Exercise.objects.filter(id__startswith='EX').count()}")
    
    if success:
        print("🎉 All exercises created successfully!")
    else:
        print("💥 Failed to create exercises")