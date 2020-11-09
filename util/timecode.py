import re
from errors import errors



def convert_timecode_to_seconds(user_time):
    """ Converts user timecode format to seconds. """

    replies = {
        "0": "Invalid Timecode",
        "1": "No decimals in the minutes pls",
        "2": "Can't have more than 60 minutes in an hour, dummy.",
        "3": "Can't have more than 60 seconds in a minute, dummy.",
        "4": "No decimals in the hours pls",
        "5": "That's a really long video. I am not bothering to download that.",
    }

    if not re.match(r"^[0-9:.]+$", user_time):
        errors.TimecodeError(replies.get("0"))
        
    temp_time = user_time.split(":")
    
    if len(temp_time) == 1:
        return float(user_time)
    
    if len(temp_time) == 2:
        if "." in temp_time[0]:
            raise errors.TimecodeError(replies.get("1"))
                

        if int(temp_time[0]) >= 60:
            raise errors.TimecodeError(replies.get("2"))

        if float(temp_time[1]) >= 60:
            raise errors.TimecodeError(replies.get("3"))

        mins = int(temp_time[0]) * 60
        secs = float(temp_time[1]) 
        return mins + secs
    
    if len(temp_time) == 3:
        if "." in temp_time[0]:
            raise errors.TimecodeError(replies.get("4"))
        
        if int(temp_time[0]) > 5:
            raise errors.TimecodeError(replies.get("5"))

        if "." in temp_time[1]:
            raise errors.TimecodeError(replies.get("1"))

        if int(temp_time[1]) >= 60:
            raise errors.TimecodeError(replies.get("2"))

        if float(temp_time[2]) >= 60:
            raise errors.TimecodeError(replies.get("3"))
            

        hrs = int(temp_time[0]) * 60 * 60
        mins = int(temp_time[1]) * 60
        secs = float(temp_time[2])
        return hrs + mins + secs


def check_valid_timecode(memeName, start, end):
    if not memeName.isalnum():
        raise errors.TimecodeError("Meme name needs to be alphanumeric")

    if not start or not end:
        raise errors.TimecodeError("No start and end timestamps.")

    start = convert_timecode_to_seconds(start)
    end = convert_timecode_to_seconds(end)

    if start > end:
        raise errors.TimecodeError("End timestamp needs to be after starting timestamp. Try again.")

    return (start, end)
            

