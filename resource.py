# -*- coding: utf-8 -*-
import datetime
from dateutil import rrule
from dateutil.relativedelta import relativedelta
from openerp import api
from openerp.osv import fields, osv
from openerp.tools.float_utils import float_compare
from openerp.tools.translate import _
import pytz,math,copy

@api.model
def _tz_get(self):
    # put POSIX 'Etc/*' entries at the end to avoid confusing users - see bug 1086728
    return [(tz,tz+','+datetime.datetime.now(pytz.timezone(tz)).strftime('%z')) for tz in sorted(pytz.all_timezones) if not tz.startswith('Etc/')]


class resource_calendar_attendance_local(osv.osv):
    _name = "resource.calendar.attendance.local"
    _description = "Work Detail"
    
        
    _columns = {
        'name' : fields.char("Name", required=True),        
        'dayofweek_local': fields.selection([('0','Monday'),('1','Tuesday'),('2','Wednesday'),('3','Thursday'),('4','Friday'),('5','Saturday'),('6','Sunday')], 'Day of Week', required=True, select=True),
        'date_from' : fields.date('Starting Date'),
        'local_hour_from' : fields.float('Work from', required=True, help="Start and End time of working.", select=True),
        'local_hour_to' : fields.float("Work to", required=True),
        'calendar_id_local' : fields.many2one("resource.calendar", "Resource's Calendar", required=True,copy=False,ondelete='cascade'),
    }
    _order = 'dayofweek_local, local_hour_from'

    _defaults = {
        'dayofweek_local' : '0',
    }


    def check_hour_from_to(self, cr, uid, ids, context=None):
        for check in self.browse(cr, uid, ids, context=context):
            #print "check.local_hour_from",check.local_hour_from
            #print "check.local_hour_to",check.local_hour_to
            if (check.local_hour_from >= 24.0 or check.local_hour_from < 0.0) or (check.local_hour_to >= 24.0 or check.local_hour_to < 0.0) or (check.local_hour_from > check.local_hour_to):
                return False
        return True

    _constraints = [
        (check_hour_from_to, 'Error! HOURS cannot be greater than 23:59 or less than 00:00.  HOURS FROM has to be less than HOURS TO', ['local_hour_from', 'local_hour_to'])
    ]

    def create(self,cr,uid,vals,context=None):
        #print "==========in create of resource.calendar.attendance.local",vals
        return super(resource_calendar_attendance_local, self).create(cr,uid,vals,context)
    
    def write(self,cr,uid,ids,vals,context=None):
        #print "==========in write of resource.calendar.attendance.local",vals
        return super(resource_calendar_attendance_local, self).write(cr,uid,ids,vals,context)
    


class resource_calendar(osv.osv):
    _inherit='resource.calendar'
    
    
    _columns={'timezone':fields.selection(_tz_get,  'Machine Timezone', size=64,required=True),
              'attendance_ids_local': fields.one2many('resource.calendar.attendance.local', 'calendar_id_local', 'Working Time', copy=True),
              }
    _defaults={'timezone':lambda self, cr, uid, context: context.get('tz', 'GMT'),
               }
    
    def _get_hour_weekday(self,cr,uid,time_diff_float,local_attendance):
        '''returns attendance_ids(UTC timings) from local_attendance timings'''
        res=[]
        #print local_attendance
        if local_attendance is None: local_attendance=[]
        for line in local_attendance:
            #print "========line====",line
            line_copy=copy.deepcopy(list(line))
            #print "========line_copy====",line_copy
            # for clarification http://stackoverflow.com/questions/184643/what-is-the-best-way-to-copy-a-list
            #print "=====id(line),id(line_1),id(line_copy)",id(line),id(line_1),id(line_copy)
            dict=line_copy[2]
            #print "=======dict====",dict
            dict['dayofweek']=dict.pop('dayofweek_local')
            dict['hour_from']=dict.pop('local_hour_from')
            dict['hour_to']=dict.pop('local_hour_to')
            #print "=======dict====",dict
            hour_from=time_diff_float+dict['hour_from']
            hour_to=time_diff_float+dict['hour_to']
            dayofweek=int(dict['dayofweek'])
            date_from=dict.get('date_from',False)
            #print "=====hour_from,hour_to,dayofweek,date_from====",hour_from,hour_to,dayofweek,date_from
            if 0.0<=hour_from and hour_to<=24.0:
                dict['hour_from']=hour_from if hour_from !=24.0 else 23.99
                dict['hour_to']=hour_to if hour_to !=24.0 else 23.99
                dict['dayofweek']=str(dayofweek)
            if 24.0<=hour_from and 24.0<hour_to<48.0:
                dict['hour_from']=hour_from - 24.0 if (hour_from-24.0)!=24.0 else 23.99
                dict['hour_to']=hour_to - 24.0 if (hour_to-24.0)!=24.0 else 23.99
                dict['dayofweek']=str(dayofweek + 1 if dayofweek <6 else 0)
                if date_from:dict['date_from']=date_from + datetime.timedelta(days=1) 
            if -24.0<=hour_from<0.0 and -24.0<=hour_to<0.0:
                dict['hour_from']=hour_from + 24.0 
                dict['hour_to']=hour_to + 24.0
                dict['dayofweek']=str(dayofweek - 1 if dayofweek >0 else 6)
                if date_from: dict['date_from']=date_from + datetime.timedelta(days=-1)
            if 0.0<=hour_from<=24.0 and 24.0<hour_to<48.0:
                dict['hour_from']=hour_from if hour_from !=24.0 else 23.99
                dict['hour_to']=23.99
                dict['dayofweek']=str(dayofweek)
                new_dict={'name':dict['name'],
                          'dayofweek':str(dayofweek + 1 if dayofweek <6 else 0),
                          'date_from':date_from if date_from else False,
                          'hour_from':0.0,
                          'hour_to':hour_to - 24.0 if (hour_to-24.0)!=24.0 else 23.99,
                          }
                res.append((0,0,new_dict))
            if -24.0<=hour_from<0.0 and 0.0<=hour_to<=24.0:
                dict['hour_from']=0.0
                dict['hour_to']=hour_to
                dict['dayofweek']=str(dayofweek)
                new_dict={'name':dict['name'],
                          'dayofweek':str(dayofweek - 1 if dayofweek >0 else 6),
                          'date_from':date_from - datetime.timedelta(days=-1) if date_from else False,
                          'hour_from':hour_from + 24.0,
                          'hour_to':23.99,
                          }
                res.append((0,0,new_dict))
            
            line_copy[2]=dict
            res.append(line_copy)
        #print "----------------res",res
        return res
    
    
    def _get_time_diff_float(self, cr, uid,timezone):
        '''returns the time difference between the timezone and UTC'''
        time_diff=int(datetime.datetime.now(pytz.timezone(timezone)).strftime('%z'))
        sign = lambda x: math.copysign(1, x)*(-1.0)
        time_diff_float=sign(time_diff)*((abs(time_diff)-abs(time_diff)/100*100)/60.0+abs(time_diff)/100)
        return time_diff_float
    
    
    def create(self,cr,uid,vals,context=None):
        time_diff_float=self._get_time_diff_float(cr, uid,vals.get('timezone'))
        #print "==========in create of resource.calendar",vals
        vals['attendance_ids']=self._get_hour_weekday(cr,uid,time_diff_float,vals.get('attendance_ids_local'))
        #print "==========in create of resource.calendar final",vals
        return super(resource_calendar, self).create(cr,uid,vals,context)
    
    def write(self,cr,uid,ids,vals,context=None):
        res=super(resource_calendar, self).write(cr,uid,ids,vals,context)
        #print "==========in write of resource.calendar==vals,ids",vals,ids
        #print "==========in read of resource.calendar",self.read(cr,uid,ids)
        obj=self.browse(cr,uid,ids[0],context)
        cr.execute("delete from resource_calendar_attendance where calendar_id=%s" %(obj.id))
        local_attendance=[]
        time_diff_float=self._get_time_diff_float(cr, uid,obj.timezone)
        for line in obj.attendance_ids_local:
            vals_local=(0, 0, {'dayofweek_local': line.dayofweek_local, 'local_hour_to': line.local_hour_to, 'name': line.name, 'local_hour_from': line.local_hour_from, 'date_from': line.date_from,'calendar_id':line.calendar_id_local.id})
            local_attendance.append(vals_local)
        attendance=self._get_hour_weekday(cr,uid,time_diff_float,local_attendance)
        for line in attendance:
            self.pool.get("resource.calendar.attendance").create(cr,uid,line[2],context)
        return res
    
    
    
    def get_working_intervals_of_day(self, cr, uid, id, start_dt=None, end_dt=None,
                                     leaves=None, compute_leaves=False, resource_id=None,
                                     default_interval=None, context=None):
        """ Get the working intervals of the day based on calendar. This method
        handle leaves that come directly from the leaves parameter or can be computed.

        :param int id: resource.calendar id; take the first one if is a list
        :param datetime start_dt: datetime object that is the beginning hours
                                  for the working intervals computation; any
                                  working interval beginning before start_dt
                                  will be truncated. If not set, set to end_dt
                                  or today() if no end_dt at 00.00.00.
        :param datetime end_dt: datetime object that is the ending hour
                                for the working intervals computation; any
                                working interval ending after end_dt
                                will be truncated. If not set, set to start_dt()
                                at 23.59.59.
        :param list leaves: a list of tuples(start_datetime, end_datetime) that
                            represent leaves.
        :param boolean compute_leaves: if set and if leaves is None, compute the
                                       leaves based on calendar and resource.
                                       If leaves is None and compute_leaves false
                                       no leaves are taken into account.
        :param int resource_id: the id of the resource to take into account when
                                computing the leaves. If not set, only general
                                leaves are computed. If set, generic and
                                specific leaves are computed.
        :param tuple default_interval: if no id, try to return a default working
                                       day using default_interval[0] as beginning
                                       hour, and default_interval[1] as ending hour.
                                       Example: default_interval = (8, 16).
                                       Otherwise, a void list of working intervals
                                       is returned when id is None.

        :return list intervals: a list of tuples (start_datetime, end_datetime)
                                of work intervals """
        if isinstance(id, (list, tuple)):
            id = id[0]

        # Computes start_dt, end_dt (with default values if not set) + off-interval work limits
        work_limits = []
        if start_dt is None and end_dt is not None:
            start_dt = end_dt.replace(hour=0, minute=0, second=0)
        elif start_dt is None:
            start_dt = datetime.datetime.now().replace(hour=0, minute=0, second=0)
        else:
            work_limits.append((start_dt.replace(hour=0, minute=0, second=0), start_dt))
        if end_dt is None:
            end_dt = start_dt.replace(hour=23, minute=59, second=59)
        else:
            work_limits.append((end_dt, end_dt.replace(hour=23, minute=59, second=59)))
        assert start_dt.date() == end_dt.date(), 'get_working_intervals_of_day is restricted to one day'

        intervals = []
        work_dt = start_dt.replace(hour=0, minute=0, second=0)
        #print "workdate---------------------------",work_dt,start_dt,datetime.datetime.now().replace(hour=0, minute=0, second=0),work_limits
        # no calendar: try to use the default_interval, then return directly
        if id is None:
            if default_interval:
                working_interval = (start_dt.replace(hour=default_interval[0], minute=0, second=0), start_dt.replace(hour=default_interval[1], minute=0, second=0))
            intervals = self.interval_remove_leaves(working_interval, work_limits)
            return intervals
        ##harsh## edited int(calendar_working_day.hour_from) to include minutes in a working day interval (calendar_working_day.hour_from)
        working_intervals = []
        #print "----------------start_dt.weekday()",start_dt.weekday()
        for calendar_working_day in self.get_attendances_for_weekdays(cr, uid, id, [start_dt.weekday()], context):
            hour_from=calendar_working_day.hour_from
            hour_to=calendar_working_day.hour_to
            working_interval = (
                work_dt.replace(hour=int(hour_from),minute=int((hour_from-int(hour_from))*60)),
                work_dt.replace(hour=int(hour_to),minute=int((hour_to-int(hour_to))*60))
            )
            #print "---------------------------------------------working_intervals",working_interval
            working_intervals += self.interval_remove_leaves(working_interval, work_limits)
        #print "intervals in def get_working_intervals_of_day",working_intervals
        # find leave intervals
        if leaves is None and compute_leaves:
            leaves = self.get_leave_intervals(cr, uid, id, resource_id=resource_id, context=None)
            #print "leaves============",leaves

        # filter according to leaves
        for interval in working_intervals:
            work_intervals = self.interval_remove_leaves(interval, leaves)
            intervals += work_intervals
        #print "intervals after leaves in def get_working_intervals_of_day",intervals
        return intervals

    
    def interval_get_multi(self, cr, uid, date_and_hours_by_cal, resource=False, byday=True):
        """ Used in mrp_operations/mrp_operations.py (default parameters) and in
        interval_get()
        
        :deprecated: OpenERP saas-3. Use schedule_hours instead. Note:
        Byday was not used. Since saas-3, counts Leave hours instead of all-day leaves."""
        res = {}
        ##harsh## added resource_in_dict to get resource/workcenter for which interval is being calculated
        print "=========0000000000=========interval_get_multi======="
        for res_dict in date_and_hours_by_cal:
            print "==========111111"
            resource_in_dict=False
            if len(res_dict)==4:dt_str, hours, calendar_id,resource_in_dict=res_dict
            else:dt_str, hours, calendar_id=res_dict
            print "==========222222222"
            result = self.schedule_hours(
                cr, uid, calendar_id, hours,
                day_dt=datetime.datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S').replace(second=0),
                compute_leaves=True, resource_id=resource_in_dict or resource,
                default_interval=(8, 16)
            )
            print "=========3333333333"
            res[(dt_str, hours, calendar_id)] = result
            print "=========444444444444"
        return res

class mrp_production_workcenter_line(osv.osv):
    _inherit='mrp.production.workcenter.line'

    def _get_date_end(self, cr, uid, ids, field_name, arg, context=None):
        """ Finds ending date.
        @return: Dictionary of values.
        """
        ops = self.browse(cr, uid, ids, context=context)
        ##harsh## added op.workcenter_id.resource_id.id in date_and_hours_by_cal to send resource_id to 
        ######### following methods(basically to send to def get_leave_intervals)
        date_and_hours_by_cal = [(op.date_planned, op.hour, op.workcenter_id.calendar_id.id,op.workcenter_id.resource_id.id or False) for op in ops if op.date_planned]
        #print "workcenters new00000000.......===============",[op.workcenter_id.name for op in ops if op.date_planned]
        intervals = self.pool.get('resource.calendar').interval_get_multi(cr, uid, date_and_hours_by_cal)
        print "intervals......",intervals
        res = {}
        for op in ops:
            res[op.id] = False
            if op.date_planned:
                i = intervals.get((op.date_planned, op.hour, op.workcenter_id.calendar_id.id))
                if i:
                    #print "in _get_date_end i[-1][1].strftime('%Y-%m-%d %H:%M:%S')",i[-1][1].strftime('%Y-%m-%d %H:%M:%S')
                    res[op.id] = i[-1][1].strftime('%Y-%m-%d %H:%M:%S')
                else:
                    res[op.id] = op.date_planned
        return res
    
    _columns={'date_planned_end': fields.function(_get_date_end, string='End Date', type='datetime')
              }