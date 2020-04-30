try:
    from win10toast import ToastNotifier
except:
    pass

def Toast(message, icon):
    try:
        toaster = ToastNotifier()
        toaster.show_toast("New device connected",
                        "client description",
                        icon_path=None,
                        duration=5,
                        threaded=True)
    except:
        pass

    #toast mac


