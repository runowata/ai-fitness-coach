#!/usr/bin/env python3
"""
Quick verification that AI generation is working after the fix
This script guides you through testing the AI generation manually
"""
import webbrowser
import time

def main():
    print("🚀 AI GENERATION TEST VERIFICATION")
    print("=" * 50)
    
    print("\n📋 TESTING STEPS:")
    print("1. We just deployed the working AI integration from archive folder")
    print("2. Need to verify it works by testing actual user flow")
    print("3. This will test the complete AI generation pipeline")
    
    print("\n🔧 WHAT WAS FIXED:")
    print("✅ Added AIClientFactory with proper OpenAI client")
    print("✅ Added PromptManager for file-based prompts")  
    print("✅ Added OnboardingDataProcessor")
    print("✅ Copied all archetype prompts (bro, sergeant, intellectual)")
    print("✅ Fixed timeout handling and JSON parsing")
    print("✅ Switched to o1 model like in working version")
    
    print("\n🧪 MANUAL TEST PROCEDURE:")
    print("1. Opening registration page...")
    
    # Open the registration page
    url = "https://ai-fitness-coach-ttzf.onrender.com/users/register/"
    webbrowser.open(url)
    
    print(f"🌐 Opened: {url}")
    print("\n📝 PLEASE DO THE FOLLOWING:")
    print("1. ✅ Register a new test account")
    print("2. ✅ Complete the onboarding questionnaire") 
    print("3. ✅ Wait for AI to generate your workout plan")
    print("4. ✅ Check if you get redirected to dashboard with plan")
    
    print("\n🎯 SUCCESS INDICATORS:")
    print("✅ Onboarding completes without errors")
    print("✅ You see 'AI Analysis' loading screen")
    print("✅ You get redirected to dashboard")
    print("✅ Dashboard shows your personalized workout plan")
    print("✅ Plan has exercises with sets/reps/rest times")
    print("✅ Plan matches your selected archetype (bro/sergeant/intellectual)")
    
    print("\n❌ FAILURE INDICATORS:")  
    print("❌ Stuck on onboarding loading screen")
    print("❌ Error message during AI generation")
    print("❌ Empty dashboard with no workout plan")
    print("❌ Generic plan not matching your preferences")
    
    print("\n⏱️  EXPECTED TIMELINE:")
    print("• Registration: 30 seconds")
    print("• Onboarding: 2-3 minutes")  
    print("• AI Generation: 30-60 seconds")
    print("• Dashboard redirect: immediate")
    
    input("\n⏸️  Press Enter when you've completed the test...")
    
    print("\n📊 TEST RESULTS:")
    result = input("Did the AI generation work? (y/n): ").lower()
    
    if result == 'y':
        print("\n🎉 SUCCESS! AI generation is now working!")
        print("✅ The archive version integration was successfully restored")
        print("✅ OpenAI API key is working on production")
        print("✅ All components (AIClientFactory, PromptManager, etc.) are functional")
        
        archetype = input("\nWhich archetype did you choose? (bro/sergeant/intellectual): ").lower()
        if archetype in ['bro', 'sergeant', 'intellectual']:
            print(f"✅ Great! The {archetype} archetype prompt was loaded correctly")
        
        print("\n🎯 NEXT STEPS:")
        print("• Test different archetypes to verify all prompts work")
        print("• Check that video playlists are generated correctly")
        print("• Verify achievement system triggers after workouts")
        
    else:
        print("\n❌ AI generation still not working. Let's diagnose...")
        error = input("What error did you see? (describe briefly): ")
        print(f"\n🔍 ERROR: {error}")
        
        print("\n🛠️  NEXT DEBUGGING STEPS:")
        print("1. Check Render logs for Python errors")
        print("2. Verify OPENAI_API_KEY is set in Render environment")
        print("3. Check if prompts directory was deployed correctly")
        print("4. Verify database migrations ran successfully")
        
        print("\n📋 RENDER COMMANDS TO RUN:")
        print("• Check logs: View logs in Render dashboard")
        print("• Test management command: python manage.py test_ai_generation")
        print("• Check environment: printenv | grep OPENAI")

if __name__ == "__main__":
    main()