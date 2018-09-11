import discord
from discord.ext import commands
from pint import UnitRegistry
from pint import errors

import traceback
import sys

ureg = UnitRegistry()
Q_ = ureg.Quantity

units = {
    'k': ureg.kelvin,
    'c': ureg.degC,
    'f': ureg.degF,
    'm': ureg.meter,
    'mi': ureg.mile,
    'cm': ureg.centimeter,
    'mm': ureg.millimeter,
    'km': ureg.kilometer,
    'ft': ureg.foot,
    'in': ureg.inch,
    'yd': ureg.yard,
    'kph': (ureg.kilometer / ureg.hour),
    'kps': (ureg.kilometer / ureg.second),
    'mps': (ureg.meter / ureg.second),
    'mph': (ureg.mile / ureg.hour),
    'l': ureg.litre,
    'ml': ureg.millilitre,
    'cl': ureg.centilitre,
    'dl': ureg.decilitre,
    'floz': ureg.floz,
    'kg': ureg.kilogram,
    'lb': ureg.pound,
    'g': ureg.gram,
    'oz': ureg.ounce
}

class Converter:
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name='convert',
                      description='Converts between given units .convert <value> <unit> to <unit>',
                      brief="Converts between given units.")
    async def convert(self, value, unit, dummy, new_unit=None):
        if new_unit is None:
            await self.bot.say("Please use `.convert <value> <unit> to <new_unit>`.")
            return
        qunit = units.get(unit.lower(), None)
        qnew_unit = units.get(new_unit.lower(), None)
        if unit and new_unit:
            quant = Q_(float(value), qunit)
            try:
                new_quant = quant.to(qnew_unit)
                resp = "{:.2f}{} is equal to {:.2f}{}.".format(float(value), unit, new_quant.magnitude, new_unit)
            except errors.DimensionalityError as de:
                traceback.print_exc(file=sys.stdout)
                resp = "Conversion from " + unit + " to " + new_unit + " not possible."
            except Exception as e:
                traceback.print_exc(file=sys.stdout)
                resp = "Conversion from " + unit + " to " + new_unit + " not possible."
        else:
            resp = "Invalid Units."
        await self.bot.say(resp)
    
    @commands.command(name='units',
                      description='Lists possible units for .convert',
                      brief='Lists possible units for .convert')
    async def units(self):
        string = "```"
        for unit_abr, unit in units.items():
            string += "{:4s} - {}\n".format(unit_abr, unit)
        string += "```"
        await self.bot.say(string)

def setup(bot):
    bot.add_cog(Converter(bot))