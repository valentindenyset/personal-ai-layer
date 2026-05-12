-- Export all Apple Notes to data/notes_export/*.txt
-- Usage: osascript scripts/export_notes.applescript

set exportFolder to (POSIX path of (path to home folder)) & "personal-ai-layer/data/notes_export/"

do shell script "mkdir -p " & quoted form of exportFolder

tell application "Notes"
	repeat with theNote in every note
		set noteTitle to the name of theNote
		set noteBody to the body of theNote
		set safeTitle to do shell script "echo " & quoted form of noteTitle & " | tr -d '/:*?\"<>|\\\\' | cut -c1-80"
		set filePath to exportFolder & safeTitle & ".txt"
		do shell script "echo " & quoted form of noteBody & " > " & quoted form of filePath
	end repeat
end tell

return "Done — notes exported to " & exportFolder
