Keep in mind this is still WIP!
I created this to support me while identifying wild bees. I was really annoyed that I had to look through my microscope, then look at the identification key, back into the microscope.....
The assistant uses Gemini and Googles Text-to-Speech and Speech-to-Text services, this enables me to "talk" with the identification key.
The LLM doesnt have to do much work its mainly there to interpret the natural language user input for the python script and rephrase identification steps to a more natural language.
The assistant could help with any other identificatiopn other than bees, it just needs the identification key in the correct format (see id_key.json). Sadly I can't publish the keys I used for testing because of copyright stuff.
I used OCR and Gemini to convert pdf keys to the json format, this process also needs refinement.
Since im still a beginner at literally every aspect of this project (AI, API, Python, GitHub) feel free to leave feedback and ideas!
Things I want to implement in the future:
- make a simple GUI
- allow the script to show pictures/drawings tied to certain steps
