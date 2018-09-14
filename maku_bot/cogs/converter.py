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
    'nmi': ureg.nautical_mile,
    'ft': ureg.foot,
    'in': ureg.inch,
    'yd': ureg.yard,
    'kph': (ureg.kilometer / ureg.hour),
    'kt': ureg.knot,
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
    'oz': ureg.ounce,
    'sv': ureg.sievert,
    'usv': ureg.microsievert,
    'gy': ureg.gray,
    'ugy': ureg.microgray,
    'rem': ureg.rem,
    'rads': ureg.rads,
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
        if all([qunit, qnew_unit]):
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
            if unit.lower() in ('banana', 'bananas'):
                if await self.banana_exception(value, qnew_unit):
                    return
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

    async def banana_exception(self, value, new_unit):
        rad_banana = 0.1 * ureg.microgray
        weight_banana = 118 * ureg.gram
        length_banana = 8 * ureg.inch
        val = float(value)
        new_quant = None
        try:  # try radiation first
            qval = val * rad_banana
            new_quant = qval.to(new_unit)
        except errors.DimensionalityError as de:
            try:  # try length next
                qval = val * length_banana
                new_quant = qval.to(new_unit)
            except errors.DimensionalityError as de:
                try:  # try weight next
                    qval = val * weight_banana
                    new_quant = qval.to(new_unit)
                except errors.DimensionalityError as de:
                    pass
        if new_quant:
            resp = "{:.2f}{} is equal to {:.2f}{}.".format(val, 'bananas', new_quant.magnitude, new_unit)
            await self.bot.say(resp)
            return True
        return False


def setup(bot):
    bot.add_cog(Converter(bot))