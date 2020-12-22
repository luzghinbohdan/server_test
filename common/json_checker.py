def check_difference(orig, new):
    diff = {}
    if type(orig) != type(new):
        # print "Type difference"
        return True
    else:
        if type(orig) is dict and type(new) is dict:
            # print "Types are both dicts"
            # Check each of these dicts from the key level
            diff_test = False
            for key in orig:
                result = check_difference(orig[key], new[key])
                if result != False:  # Means a difference was found and returned
                    diff_test = True
                    # print "key/Values different: " + str(key)
                    diff[key] = result
            # And check for keys in second dataset that aren't in first
            for key in new:
                if key not in orig:
                    diff[key] = ("KeyNotFound", new[key])
                    diff_test = True

            if diff_test:
                return diff
            else:
                return False
        else:
            # print "Types were not dicts, likely strings"
            if str(orig) == str(new):
                return False
            else:
                return (str(orig), str(new))
    return diff