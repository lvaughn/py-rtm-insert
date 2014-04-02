py-rtm-insert
=============

Drafts/Pythonista/Remember The Milk script to bulk insert tasks.  A quick hack to do bulk adds of 
tasks to [Remember The Milk](http://rememberthemilk.com).  It's designed to 
be used inside of [Pythonista](http://omz-software.com/pythonista/) on iOS (called by 
[Drafts](http://agiletortoise.com/drafts/), but that's flexible).

I'm not sure if it's useful to anyone but me, but it fits my work
flow of adding a bunch of tasks at once when planning my day,
and perhaps it will be useful to other people. I find this easier for
bulk task capture than RTM's iOS app.

# Required #
* Pythonista
* Drafts (or other app that sends can send text via a URL)
* An API Key from Remember the Milk (they are free, the instructions on the 
  RTM website)

# Install #

1. Get an [API\_KEY and a SHARED\_SECRET](https://www.rememberthemilk.com/services/api/keys.rtm)
2. Fix the values for API\_KEY and SHARED\_SECRET near the top of `py_rtm_insert.py`
3. Copy `py_rtm_insert.py` file in to Pythonista, naming it "SendToRTM"
4. Create a custom URL action in Drafts with the URL (named whatever you want)

        pythonista://SendToRTM?action=run&argv=[[draft]]

From there, you can open up Drafts and enter your tasks, one per line, and then 
invoke the actions.  The first time you run the script, you'll have to log in 
to Remember The Milk, but it should save your authentication for a while after
that.

For questions, contact [Lowell Vaughn](mailto:lowell@vaughnresearch.com)
