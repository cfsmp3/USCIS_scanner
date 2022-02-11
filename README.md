# USCIS_scanner
A quick and dirty tool to analyze case status at USCIS for a given date

This is very likely useless for anyone else, but I don't want to lose it so I might as well share it.

Yes, I know the code seems to be written by a monkey. A not bright one, that also didn't care much. 

It works for my case though.

For any given date (it default to mine, so make sure you pass your case number) it will scan the cases and get some stats.

Then, for a specific form type, it will break down the current status and compare with the last run, if any.

So you can, for your specific date and case type, get an idea of where you stand and how fast, or slow, things are moving.

## Instructions
You need to have Python and Pip installed first.
https://realpython.com/installing-python/#how-to-install-python-on-windows

Then from the command line, navigate to this folder and run:
```
pip install -r requirements.txt
```

And then, for example to find all cases in LIN21111 batch, run:
```
python ./lin.py --case LIN21111XXXXX
```

You can add arguments like follows:
```
    "--case": "Reference case number, used to extract date to process.", default="LIN21111XXXXX",
    "--form","Form type we care about when updating current state",default="I-485",
    "-u","Go over the list of Unknown events and try to process them again (useful only if there's been changes in code)",default="False"
```

