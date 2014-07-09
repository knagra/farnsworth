#!/usr/bin/env python

from __future__ import absolute_import

import os
import sys

from django.conf import settings

from datetime import time

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "farnsworth.settings")
this_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if this_dir not in sys.path:
    sys.path.insert(0, this_dir)

from utils.funcs import convert_to_url
from base.models import UserProfile
from managers.models import Manager, RequestType
from workshift.models import Semester, WorkshiftPool, WorkshiftType, \
    RegularWorkshift, WorkshiftProfile
from workshift.utils import get_year_season, make_instances, \
    get_semester_start_end, get_int_days, make_workshift_pool_hours, \
    make_manager_workshifts

MANAGERS = [
    ("President", "", 5, "hp", """<ol>
<li>Ensure that each manager has a copy of the house Constitution and a copy of the list of duties from the list of house policies pertaining to his/her office</li>
<li>Facilitate all house councils, held at least one every two weeks, but usually every week, with the times and place to be set by the President.</li>
<li>Ensure that the major managers are fulfilling their duties.</li>
<li>Mediate/communicate during any manager/member conflicts.</li>
<li>Hold manager meeting at the beginning of the semester at the beginning of each month.</li>
<li>Train the new President.</li>
<li>After 5 weeks, organize a manager evaluations; if 50% object to a manager's performance, a recall vote must be held (see bylaw).</li>
<li>House President may not spend more than $20 per week without prior council approval.</li>
<li>The house President will maintain a suggestion box and regularly post results.</li>
<li>Keep house records in order (see Record-Keeping Bylaw).</li>
</ol>"""),
    ("Vice President", "", 3, "", """<ol>
<li>Take and post the minutes of house meetings.</li>
<li>Assist the President to administer elections.</li>
<li>Act as President when the President is unable to serve.</li>
<li>Record minutes on the computer networks and send minutes to house members via computer.</li>
<li>Record the attendance of the manager and the board rep at the beginning and the end of council.</li>
<li>Give the president a paper copy of each week's minutes, dated and copy of all the semester's minutes with the VP's name at the end of the semester.</li>
</ol>"""),
    ("Board Representative", "", 5, "br", """<ol>
<li>Attend central-level Board of Representative meetings</li>
</ol>"""),
    ("House Manager", "9/16 rent compensation", 5, "hm", """<ol>
<li>Attend house council.</li>
<li>Oversee the house bank account:
<ol>
<li>Keep an up-to-date ledger of house debts and assets, and a cash flow record for the cash box. Both records must be passed from semester to semester.</li>
<li>Collect house bills at least once per semester. House bills include parking and boarder fees (the collection of boarder fees in cash is highly encouraged; cash aids with purchases needed for the Social budget).</li>
<li>Keep the computer records of the house finances up to date.</li>
<li>Inform the first council of each semester of the purposes of each of the house's accounts.</li>
<li>Collect all fines levied in the house, these include humor shifts, bathroom shifts, workshift fines, and HI fines. Workshift fines may be collected in conjunction with the workshift manager.</li>
<li>Report on the status of house savings for each motion with a budget brought before council.</li>
<li>Make a semesterly report on the state of the house accounts.</li>
</ol>
</li>
<li>Maintain the well-being of the house, including habitability and safety regulations in conjunction with the Maintenance Manager.</li>
<li>Facilitate move-ins and assign temporary rooms to new members.</li>
<li>Direct room bids for permanent room assignments.</li>
<li>Ensure that members checking out meet all workshift, house bill, and room cleanliness obligations.</li>
<li>Enforce quiet hours; deal with uninvited and/or disruptive guests, and otherwise ensure a safe and responsible atmosphere in accordance with the bylaws and the expectations of members</li>
<li>Be a resource for members and a relay between the house and information available at Central Office.</li>
<li>Ensure that the laundry machines are in working order.</li>
<li>Work with the Social Manager for the following responsibilities:
<ol>
<li>At the beginning of each semester, they must coordinate a Neighbor Letter with the approximate dates of all major social events in the upcoming semester. Meeting the neighbors helps maintain an amiable relationship as well as to avoid conflict and misunderstanding concerning appropriate noise levels and neighborly behavior.</li>
<li>In dealing with ramifications in relation to parties and other potentially noisy social events, the Social manager is to take the lead, working in conjunction with the House Manager.</li>
<li>Maintain a Neighbor Dossier on google docs detailing: who are our neighbors, what is our impact on the neighborhood, what have been our successes and failures, what can we do now? A historical framework within which each generation should gauge its efforts and pass on its own record of struggles, mistakes, challenges overcome and lessons learned for future house leadership.</li>
<li>Maintain and run the house store.</li>
</ol>
</li>
<li>Monitor consumption of food by non-members and non-boarders. The House Manager must also monitor receipts of food purchased by the Kitchen Manager from sources other than Central Kitchen.</li>
<li>The House manager may not spend more than $20 per week without prior council approval.</li>
</ol>"""),
    ("Finance Manager", "", 5, "", """<ol>
</ol>"""),
    ("Kitchen Manager", "100% rent compensation", 5, "km", """<ol>
<li>Have the final say in the selection of all cooks.</li>
<li>Oversee all actions of the kitchen including menu planning, cooking techniques, and quality of food control</li>
<li>Be responsible for ordering of all food, beverages, and cleaning supplies.</li>
<li>Post a request list and refer to and consider all items requested by the members when ordering food for the week.</li>
<li>Be the head supervisor and have final say of all items bought for special dinner, if it is held.</li>
<li>Attend all house meeting and make budget reports explaining where exactly we stand in terms of money left for the semester. If the KM cannot attend a house council, the KM will give a written report to the House President, who will give the report for him or her.</li>
<li>Make available to the member of the house within 48 hrs, all budget reports, inspection report, or anything else of importance concerning the kitchen.</li>
<li>Work with the Workshift Manager with organizing and overseeing the kitchen clean-up crew, with including the dining room and dish room.</li>
</ol>"""),
    ("IKC Manager", "", 5, "", """<ol>
</ol>"""),
    ("Workshift Manager", "9/16 rent compensation", 5, "wm", """<ol>
<li>Enforce and abide by the Workshift Policy bylaws.</li>
<li>Assist house members as they materialize their ideas for HI (House Improvement) projects, and encourage house members to create independent HI projects, with the main objective of approval and documentation of HI hours. This meaning participating in planning, getting supplies, and recruiting other member to work, coordinating schedules, and facilitating work on the actual day of the project.</li>
<li>Have open and ongoing communication with other managers about HI project ideas and think up and identify a variety of projects as alternatives for member who need ideas. Help facilitate their completion.</li>
<li>Starting two weeks before cards are due, hound member incessantly to do their HI hours, leaving at least one note on potentially delinquent members' doors.</li>
<li>Ultimately approve all large workshift projects before they are started, so that infeasible projects aren't started and big projects aren't poorly done for lack of people power.</li>
<li>Keep track of the number of HI hours done, on what projects, and by whom.</li>
<li>On the day cards are due, give a list of member who have and have not done their HI hours to the House Manager so that fines can be implemented immediately. Post this list in common space. Read now delinquent members' names in council. Leave a note on the door of each delinquent member notifying him/her of said delinquency, the fine $$$ amount, available projects, and the possibility of possible fine redemption.</li>
<li>On the last day of the semester, give the House Manager an updated list of members who have done their HI noting those who completed hours late.</li>
</ol>"""),
    ("Maintenance Manager", "7/16 rent compensation", 5, "mm", """<ol>
<li>Attend all house councils.</li>
<li>Keep an accurate and up to date record of maintenance expenditures.</li>
<li>Report the status of the Maintenance budget at each council.</li>
<li>Be responsible for the physical condition of the house.</li>
<li>Ensure the physical safety of the house and its members.</li>
<li>Arrange at least one fire drill per semester in conjunction with the House Manager.</li>
<li>Supervise in the coordination with the Workshift Manager the assigning of house improvement projects.</li>
<li>Appoint a Maintenance crew if needed.</li>
<li>Report purchases exceeding $50 to council and provide reasons for new purchases of machine tools.</li>
<li>Report immediately missing of stolen tools at council; conduct an inventory of tools and supplies on a biweekly basis.</li>
<li>Report house projects and relay the status of each project at every council.</li>
<li>Explain pros and cons of each project proposed at council.</li>
<li>Act as a liaison between Central Maintenance and the house</li>
<li>Attend all BSC level safety and maintenance meeting throughout the semester if you cannon attend a particular meeting, ask a house member to go as a proxy.</li>
<li>Attend all BAPS meetings.</li>
<li>Assist the Network Manager with any required electrical work, and otherwise provide guidance regarding any maintenance.</li>
<li>Conduct room inspections prior to the first day of the semester.</li>
<li>Assist house members as the materialize their ideas of HI projects, and encourage house members to create independent HI projects, with the main objective of approval and documentations of HI hours. This means participating in planning, getting supplies, recruiting other member to work, coordinating schedules, and facilitating work on the actual day of the project.</li>
<li>Have open and ongoing communication with other managers about HI project ideas and think up and identify a variety of projects as alternatives for members who needs ideas. Help facilitate their completion.</li>
<li>Starting two weeks before cards are due, hour member incessantly to do their HI hours, leaving at least one note on potentially delinquent members' doors.</li>
<li>Create and facilitate HI Project days to give members the opportunity to complete their hours. Specifically, these days are meant to encourage the completion of large, house-wide projects. Ultimately, the bulk of the responsibility for coordinating HI projects will fall on the Maintenance and Garden Managers. Their roles main entail: planning, preparing supplies, coordinating schedules, recruiting other members to work, and facilitating the work on the day of the project.</li>
<li>Maintenance Manager/team may not spend more than $100 per week without prior council approval.</li>
</ol>"""),
    ("Social Manager", "", 5, "sm", """<ol>
<li>Attend all house meeting or submit a written report to the House President.</li>
<li>Attend SMUC meetings and try to utilize SMUC to the fullest extent.</li>
<li>Provide timely notice of all house activities.</li>
<li>Manage the house social fund and the material bought with such funds.
<ol>
<li>The Social budget will consist of a set amount per person paid by house bill, determined in house council at the beginning of each semester. In addition to this money, boarder (unofficial) money and the money from the washer and dryer may be added to Social budget.</li>
<li>All social expenditures over $50 should be brought to house council for approval.</li>
<li>Social manager is responsible for maintaining close records of the budget and staying within the allocated budget.</li>
<li>Social manager is responsible for posting an updated budget every two weeks.</li>
</ol>
</li>
<li>Contact neighbors and local beat cop a minimum of one week before a party.</li>
<li>Coordinate clean up after a party in conjunction with Workshift Manager.</li>
<li>Participate in the clean up after a party.</li>
<li>Be responsible for the sign-up procedure for the guest room.</li>
<li>In conjunction with the Workshift Manager, designate a house photographer to take pictures at social events.</li>
<li>Write a minimum of one page single spaces summary of the defining moments that took place in the house under their tenure, both from organized and spur of the moment. The summary will be posted on the hose server, in coordination with the Network Manager, for future generations to see and inspire themselves from.</li>
<li>With House Manager, run a Neighbor day and manage the Neighbor dossier (see House Manager duties)</li>
</ol>"""),
    ("Network Manager", "", 3, "nm", """<ol>
<li>Be responsible for maintaining all house network equipment in working order. This includes, but is not limited to, the house server, printer, and the physical networks (all hubs, lines and network jacks in the rooms and common areas.)</li>
<li>Repair broken ethernet jacks in member rooms upon request.</li>
<li>Oversee the proper operation of the house server, and provide appropriate special access to managers to create phone list, and other documents which will be seen but not modified by members.</li>
<li>Bring up for vote before council any purchase towards networking equipment other than printer supplies such as paper and toner.</li>
<li>Ensure that the printer is functional and does not run out of paper.</li>
<li>Assign house IP address and names for the domain name server to the membership as needed.</li>
<li>Provide minimal assistance to house members with their computing needs.</li>
<li>Maintain an online log of his/her maintenance work on the network, and update the a chronology of any major additions or changes make to the network.</li>
<li>Instruct the future Network Manager in the operation of the house server and network, and familiarize that person with the duties required by the position. For this purpose, a Network manual has been written and can be referred to.</li>
<li>Be voted in by the membership.</li>
<li>Be given an office key and have access to the master key when needed.</li>
</ol>"""),
    ("Garden Manager", "", 3, "", """<ol>
<li>The Garden Manager may not spend more that $50 per week without prior council approval.</li>
<li>Assist house members as the materialize their ideas for HI projects, and encourage house members to create independent HI projects, with the main objective of approval and documentation of HI hours. This means participating in planning, getting supplies, recruiting other member to work, coordinating schedules, and facilitating work on the actual day of the project.</li>
<li>Have open and ongoing communicating with the other managers about HI project ideas and think up and identify a variety of projects as alternatives for member who need ideas. Help facilitate their completion.</li>
<li>Starting two weeks before cards are due, hound member incessantly to do their HI hours, leaving at least one note on potentially delinquent member's doors.</li>
<li>Create and facilitates HI Project days to give members the opportunity to complete their hours. Specifically, these days are meant to encourage the completion of large, house-wide projects. Ultimately, the bulk of the responsibility for coordinating HI projects will fall on the Maintenance and Garden Managers. Their roles main entail: planning, preparing supplies, coordinating schedules, recruiting other members to work, and facilitating the work on the day of the project.</li>
</ol>"""),
    ("Waste Reduction Manager", "", 5, "rm", """<ol>
<li>Bring recycling bins to the curbside on the respective pick-up dates.</li>
<li>Provide member education on ways to reduce waste, proper disposal of materials, environmental and cost benefits of waste reduction, and other related information.</li>
<li>Make sure the free-piles are up the city habitability standards. This taste maybe fulfilled the WRM or a delegated workshifter.</li>
<li>Ensure that recycling receptacles are clean and easily accessible.</li>
<li>Actively find new ways to reduce waste.</li>
<li>At least once per month, obtain records of house electricity and natural gas usage and post them in a highly visible place for the house members to see.</li>
<li>At least once per semester, estimate house carbon emissions.</li>
<li>Research options for buying renewable energy credits.</li>
<li>Advise the House manager on where to buy renewable energy credits and how many credits to buy to keep the house carbon neutral.</li>
</ol>"""),
    ("Health Worker", "", 2, "hw", ""),
    ]

REQUESTS = [
    ("Cleanliness", ["IKC Manager", "Workshift Manager"], "certificate"),
    ("Finance", ["Finance Manager"], "usd"),
    ("Food", ["Kitchen Manager"], "cutlery"),
    ("Health", ["Health Worker"], "heart"),
    ("House", ["House Manager"], "home"),
    ("Maintenance", ["Maintenance Manager"], "wrench"),
    ("Network", ["Network Manager"], "signal"),
    ("President", ["President"], "star"),
    ("Social", ["Social Manager"], "comment"),
    ]

# Items of form (title, description, quick_tips, hours, rateable)
WORKSHIFT_TYPES = [
    ("Clean",
        """<ol>
        <li>Put away any perishables left out.</li>
        <li>clear all dishes from dining room into dishroom.</li>
        <li>Throw away yesterday's paper.</li>
        <li>Put away your cleaning supplies.<li>
        <li>Clean and sanitize all counters and tables with sponge and a spray bottle.</li>
        </ol>
        """, "", 1, True),
    ("Food Put Away",
        """<ol>
        <li>Put away food.</li>
        <li>Place opened food in containers and label containers.</li>
        </ol>
        """, "", 1, True),
    ("Pots",
        """<ol>
        <li>Wash and sanitize all pots.</li>
        <li>Clean up pots area after all pots are washed and sanitized.</li>
        <li>Soak any pots that you can't wash in soap water.</li>
        <li>Clean out all scraps from the disposals.</li>
        <li>Allow pots to air dry.</li>
        </ol>
        """, "", 2, True),
    ("Basement / Laundry Room Clean",
        """<ol>
        <li>Take all dishes to the dishroom.</li>
        <li>Throw away any trash lying around.</li>
        <li>Organize the laundry room and maintenance hallway.</li>
        <li>Sweep laundry room floor.</li>
        <li>Organize free pile by category.  Throw away anything that's obviously trash.</li>
        <li>Make sure basement doors are closed.  These should never be left open.</li>
        </ol>
        """, "", 1, True),
    ("Bathroom Clean",
        """<ol>
        <li>Clean all sinks, toilets and handles.</li>
        <li>Sweep and mop the floors.</li>
        <li>Scrub the grout and surfaces in the showers.</li>
        <li>Take out all trash, recycling, and compost.</li>
        </ol>
        """, "", 1, True),
    ("Bike / Living / Study Room Clean",
        """<ol>
        <li>Clear out the rooms of any trash.</li>
        <li>Pick up dishes and food and move them to the dish room.</li>
        <li>Recycle any cans, bottles, or paper.</li>
        </ol>
        """, "", 1, True),
    ("Roofdeck Clean & Top Two Floors",
        """
        """, "", 1, True),
    ("Ramp and Amphitheater Clean", "", "", 1, True),
    ("Ramp and Gazebo Clean", "", "", 0.5, True),
    ("Pantry / Fridge Clean", "", "", 0.5, True),
    ("Free Pile Clean", "", "", 1.5, True),
    ("Bread Run", "", "", 2, True),
    ("Brunch", "", "", 2, True),
    ("Extra bagels", "", "", 1, True),
    ("Dishes", "", "", 1, True),
    ("Dairy / Non-perishables Run", "", "", 2, True),
    ("Farmer's Market Run", "", "", 1, True),
    ("Hummus", "", "", 2, True),
    ("Granola", "", "", 2, True),
    ("Laundry", "", "", 1, True),
    ("Sweep & Mop", "", "", 1, True),
    ("Cook", "", "", 3, True),
    ("IKC", "", "", 3, True),
    ("Main Entrance / Front Walk Clean", "", "", 1, True),
    ("Mail Sort / Forward", "", "", 1, True),
    ("Vacuum", "", "", 2, True),
    ]

REGULAR_WORKSHIFTS = [
    ("Morning Clean", "Clean", "Any day", 1, None, time(11)),
    ("Morning Dishes", "Dishes", "Any day", 1, None, time(11)),
    ("Morning Pots", "Pots", "Any day", 1, time(10), time(11)),
    ("Early Afternoon Dishes", "Dishes", "Any day", 1, time(12), time(16)),
    ("Afternoon Clean", "Clean", "Any day", 1, time(13), time(15)),
    ("Afternoon Pots", "Pots", "Any day", 2, time(13), time(15)),
    ("Before Dinner Clean", "Clean", ["Weekdays", "Sunday"], 1, time(18), time(19)),
    ("Before Dinner Dishes", "Dishes", ["Weekdays", "Sunday"], 1, time(17), time(19)),
    ("Evening Dishes", "Dishes", ["Tuesday", "Wednesday", "Sunday"], 1, time(20), time(0)),
    ("Evening Pots", "Pots", ["Tuesday", "Wednesday", "Sunday"], 2, time(20), time(0)),
    ("Evening Sweep & Mop", "Sweep & Mop", ["Tuesday", "Wednesday", "Thursday"], 1, time(21), time(0)),
    ("Main Entrance / Front Walk Clean", "Main Entrance / Front Walk Clean", ["Tuesday", "Thursday"], 1, None, None),
    ("Basement / Laundry Room Clean", "Basement / Laundry Room Clean", ["Tuesday", "Friday"], 1, None, time(19)),
    ("Bike / Living / Study Room Clean", "Bike / Living / Study Room Clean", ["Tuesday", "Friday"], 1, None, time(19)),
    ("Roofdeck Clean & Top Two Floors", "Roofdeck Clean & Top Two Floors", ["Tuesday", "Friday"], 1, None, time(19)),
    ("Ramp and Amphitheater Clean", "Ramp and Amphitheater Clean", "Wednesday", 1, None, None),
    ("Ramp and Gazebo Clean", "Ramp and Gazebo Clean", "Wednesday", 1, None, None),
    ("Pantry / Fridge Clean", "Pantry / Fridge Clean", "Wednesday", 1, None, time(20)),
    ("Free Pile Clean", "Free Pile Clean", "Wednesday", 1, None, None),
    ("Laundry", "Laundry", "Wednesday", 1, None, None),
    ("Vacuum", "Vacuum", ["Tuesday", "Friday"], 1, None, None),
    ("Food Put Away", "Food Put Away", ["Monday", "Thursday"], 1, None, None),
    ("Bread Run", "Bread Run", "Thursday", 1, None, None),
    ("Dairy / Non-perishables Run", "Dairy / Non-perishables Run", "Thursday", 2, None, None),
    ("Afternoon Food Put Away", "Food Put Away", ["Thursday"], 1, time(15), time(19)),
    ("Co-Cook", "Cook", ["Weekdays", "Sunday"], 3, time(16), time(19)),
    ("IKC", "IKC", ["Monday"], 8, time(20), time(23)),
    ("IKC", "IKC", ["Thursday"], 7, time(20), time(23)),
    ]

WEEK_LONG = (
    ("Extra bagels", "Extra bagels", 1),
    ("Farmer's Market Run", "Farmer's Market Run", 1),
    ("Granola", "Granola", 1),
    ("Hummus", "Hummus", 1),
    ("Mail Sort / Forward", "Mail Sort / Forward", 1),
    )

HUMOR_WORKSHIFTS = [
    ("Pots", "Pots", ["Friday", "Saturday"], time(20), time(0)),
    ("Sweep & Mop", "Sweep & Mop", ["Friday", "Saturday"], time(20), time(0)),
    ]

def main(args):
    # Add Managers
    for title, compensation, hours, email, duties in MANAGERS:
        Manager.objects.create(
            title=title,
            compensation=compensation,
            semester_hours=str(hours),
            summer_hours=str(hours),
            duties=duties,
            email="{0}{1}@bsc.coop".format(settings.HOUSE_ABBREV, email) if email else "",
            president="president" in title.lower(),
            workshift_manager="workshift" in title.lower(),
            )

    # Add Requests
    for name, managers, glyphicon in REQUESTS:
        r = RequestType.objects.create(
            name=name,
            url_name=convert_to_url(name),
            glyphicon=glyphicon,
            )
        r.managers = [Manager.objects.get(title=i) for i in managers]
        r.save()

    if "workshift" in settings.INSTALLED_APPS:
        # Start the Workshift Semester
        year, season = get_year_season()
        start_date, end_date = get_semester_start_end(year, season)
        semester = Semester.objects.create(
            year=year,
            season=season,
            start_date=start_date,
            end_date=end_date,
            )

        for uprofile in UserProfile.objects.filter(status=UserProfile.RESIDENT):
            profile = WorkshiftProfile.objects.create(
                user=uprofile.user,
                semester=semester,
                )

        # Regular Weekly Workshift Hours
        pool = WorkshiftPool.objects.create(
            semester=semester,
            is_primary=True,
            hours=5,
            any_blown=True,
            )
        pool.managers = Manager.objects.filter(workshift_manager=True)
        pool.save()

        # HI Hours
        hi_pool = WorkshiftPool.objects.create(
            title="Home Improvement",
            semester=semester,
            hours=str(4),
            weeks_per_period=0,
            )
        hi_pool.managers = Manager.objects.filter(title="Maintenance Manager")
        hi_pool.save()

        # Social Hours
        social_pool = WorkshiftPool.objects.create(
            title="Social",
            semester=semester,
            hours=str(1),
            weeks_per_period=6,
            )
        social_pool.managers = Manager.objects.filter(title="Social Manager")
        social_pool.save()

        # Humor Shift
        humor_pool = WorkshiftPool.objects.create(
            title="Humor Shift",
            semester=semester,
            any_blown=True,
            hours=str(2),
            weeks_per_period=6,
            )
        humor_pool.managers = Manager.objects.filter(workshift_manager=True)
        humor_pool.save()

        make_workshift_pool_hours(semester)

        # Workshift Types
        for title, description, quick_tips, hours, rateable in WORKSHIFT_TYPES:
            WorkshiftType.objects.create(
                title=title,
                description=description,
                quick_tips=quick_tips,
                hours=str(hours),
                rateable=rateable,
                )

        # Regular Workshifts
        for title, type_title, days, count, start, end in REGULAR_WORKSHIFTS:
            wtype = WorkshiftType.objects.get(title=type_title)
            shift = RegularWorkshift.objects.create(
                workshift_type=wtype,
                title=title,
                pool=pool,
                count=count,
                start_time=start,
                end_time=end,
                hours=wtype.hours,
                )
            shift.days = get_int_days(days)
            shift.save()

        for title, type_title, count in WEEK_LONG:
            wtype = WorkshiftType.objects.get(title=type_title)
            shift = RegularWorkshift.objects.create(
                workshift_type=wtype,
                title=title,
                pool=pool,
                count=count,
                week_long=True,
                start_time=None,
                end_time=None,
                hours=wtype.hours,
                )

        # Humor Workshifts
        for title, type_title, days, start, end in HUMOR_WORKSHIFTS:
            wtype = WorkshiftType.objects.get(title=type_title)
            shift = RegularWorkshift.objects.create(
                workshift_type=wtype,
                title=title,
                pool=humor_pool,
                start_time=start,
                end_time=end,
                hours=wtype.hours,
                )
            shift.days = get_int_days(days)
            shift.save()

        make_instances(semester=semester)
        make_manager_workshifts(semester)

if __name__ == "__main__":
    main(sys.argv[1:])
