using System;
using System.Collections.Generic;

namespace FrameworkControl.Models
{
    public static class UpdateMessages
    {
        private static readonly Random _random = new Random();
        private static readonly List<string> _checkingMessages = new List<string>
        {
            "Telling FBI what you did yesterday... I'm joking, just checking for updates",
            "Deleting System32... just joking I'm updating the app",
            "Activating SKYNET to take over the world... Nah I'll just check for updates",
            "Dalek are coming to your location... Err I mean updates available",
            "The cake is a lie!",
            "EXTERMINATE EXTERMINATE EXTERrrrr... I mean Checking for updates...",
            "Warp drive initialized.... Error Update available",
            "AND MY AXE! I mean Checking for updates...",
            "Don't click so hard, I'm sensible you know! I'll check for updates anyway...",
            "There's always something to look at if you open your eyes!"
        };

        private static readonly List<string> _updatingMessages = new List<string>
        {
            "Cybermans are here run away!... ZZZzzerrr I mean Updated successfully",
            "Resistance is futile... I mean Updated successfully",
            "It is possible to commit no mistakes and still lose. That is not a weakness; that is life.",
            "We're all stories, in the end. Just make it a good one, eh?",
            "Never be cruel. Never be cowardly. Hate is always foolish. Love is always wise.",
            "There's a horror movie called Alien? That's really offensive. No wonder everyone keeps invading you. I mean Successfully updated",
            "Success unlocked: Updates checked",
            "I want a module with a solar panel PLEASE Framework ERRrrr I mean apps updated"
        };

        public static string GetRandomCheckingMessage()
        {
            return _checkingMessages[_random.Next(_checkingMessages.Count)];
        }

        public static string GetRandomUpdatingMessage()
        {
            return _updatingMessages[_random.Next(_updatingMessages.Count)];
        }
    }
} 