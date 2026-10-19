"""For the tests: a voiceover from a made-up engine (a 2 s tone), and beats shorter than their lines."""
VOICE_ENGINE = "ffmpeg -loglevel error -y -f lavfi -i sine=frequency=440:duration=2 -f wav {out} && cat > /dev/null"
VOICE = {"first": "This line takes two seconds to say.", "second": "So does this one."}
BEATS = [("first", "", 0.2), ("second", "", 0.2), ("end", "", 0.5)]
