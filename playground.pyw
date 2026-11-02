"""playground.pyw - double-click to open the Toybox straight from this repo checkout (installed users run `psgplayground`)"""
import os
import sys

ICON = b'iVBORw0KGgoAAAANSUhEUgAAADAAAAAwCAMAAABg3Am1AAAAkFBMVEUcISYZXpkdnPgnZlAonF7VlTgA//9OO2JdTXkAev8XmfYdl/oeRzsemfqpl+U2LkqneNgQdcx5Uy+rfDcAAP9aPyJxS4T/tEAZHioAAAAuy3Dooz0aIS3Ei/4hqf4elvghsP8ZFhwdmvwbS3Yv1HQYNVPzq0AOLk7Ok/4rtGZaQia3he7IjjkAqv8dl/gcmfjyHIBRAAAAMHRSTlP/++/+//8B//4CFUz/lP////3//wH////+AP///v/+e/7/q/v/+//7//////8DL/W5YWy/AAAB5klEQVR42sWWbXeqMAyA0yrdBJnuHbAroKJOlP7/f7e0DCiult5P9/mgHE+ekwQqCaQKtkgnubYxoD7wMgxzJ1GISidc0zCmQhQOhKBxow1Q8Q0VkpCdCyKFjJQBKUsbKQgvJ+CECmUAW4RUkDLhEyTljsqGMQjTuCAl/jAB5yUR25QBC6XkyWS8htIGe2goJvAJxxRFjkJeDIKzMp5UItbCzsjA3cJ2LPAZdygWIfnOZvfrsgnz/X6+vKdYM+wzVMBe1x0hy/bZ3NrKXUEptlYcAirffxWnkFm6dwtaGbcyJehWuJFkWrhpxUfoWvEX9FOB1vAUsKzlvwhtF/5NZ8OB5zcCt9xW8xyqL0Pg1ge3fLkEwaUleIVxBlDMx8W/fG4MAhiE5GFda56QofhgFH84H3thVZ++ep764i+msDEEeDzVhtAfVJcwxH/V/fnxFNb9rfTN0B/o/ycQX6F9cBHOH0+hfd2HkiZjAbo/cXAjPAscKEyNrNUg1Kd1f/5fN4ZyCGaUvi1ggTNL7D5OPfWqG5AJBIeB4FFigivgJI0EJauHDiiHVxGcO97PMylyNXbVYI8oKtWxOioqk+MvFXmmOv53dWi2ArcDF4WgkdpJ2uUExSaPty7yxlhOcJ3xWH+Yjk9/AEml8XVmgvEbAAAAAElFTkSuQmCC'      # same icon as the launcher window - here so MiniLauncher2 picks it up when this file is dropped on an entry

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from psgplayground.playground import run

run()
