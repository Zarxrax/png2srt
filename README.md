# png2srt
This is a tool that can perform OCR (optical character recognition) on XML/PNG subtitles and output the result as an SRT file. This can be used for subtitles obtained from DVD and Blu-ray. The Google Cloud Vision API is used for the OCR, and it has very good accuracy.

# Usage
If you have ripped subtitles from a disc into a format like SUB/IDX or SUP, you can use a tool such as [Subtitle Edit](https://www.nikse.dk/subtitleedit) to convert them to XML/PNG.

Next, you have to sign up for the Google Cloud Platform, then enable the Cloud Vision API and generate an API key. This API is not free to use, but Google generally offers a pretty large amount of free credit upon signing up.

Next, you need to paste your API Key into a text file named API_KEY.txt located in the same folder as the PNG2SRT application (the file should contain ONLY your API key, and no other text). When you launch PNG2SRT, it should display your API key along the top of the window so you can ensure it was recognized correctly.

Then, you just select a folder containing your XML/PNG files. Unicode is not supported for the folder name, so please make sure the folder name uses standard ASCII characters.

The only options are the input language which your subtitles are in, and a "chunk size". The chunk size specifies how much data is sent to Google at once. If the tool appears to start working fine, but you get an error message part of the way through, you may need to reduce the chunk value to 10 or 5.

Once complete, an SRT file will be created inside of your input folder.

Sorry, but I can not commit to providing any support for this software, and it is provided as-is. 
