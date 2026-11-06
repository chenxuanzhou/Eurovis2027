"""Signal names and label enums of the voraus-AD dataset.

Vendored verbatim (classes Signals, Category, Variant, Action and the
ANOMALY_CATEGORIES list) from vorausrobotik/voraus-ad-dataset, file
voraus_ad.py, commit a91a86a642d23df58833b792a53de01edfd81abe, so that the
pipeline does not need torch. Original licence (MIT):

    Permission is hereby granted, free of charge, to any person obtaining a
    copy of this software and associated documentation files (the
    "Software"), to deal in the Software without restriction, including
    without limitation the rights to use, copy, modify, merge, publish,
    distribute, sublicense, and/or sell copies of the Software, and to
    permit persons to whom the Software is furnished to do so, subject to
    the following conditions:
    
    The above copyright notice and this permission notice shall be included
    in all copies or substantial portions of the Software.
    
    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
    OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
    MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
    CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
    TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
    SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE."""

from enum import IntEnum


class Signals:
    """Contains the signals of the robot used in the dataset."""

    TIME = "time"
    SAMPLE = "sample"
    ANOMALY = "anomaly"
    CATEGORY = "category"
    SETTING = "setting"
    ACTION = "action"
    ACTIVE = "active"
    ROBOT_VOLTAGE = "robot_voltage"
    ROBOT_CURRENT = "robot_current"
    IO_CURRENT = "io_current"
    SYSTEM_CURRENT = "system_current"
    TARGET_POSITION_1 = "target_position_1"
    TARGET_VELOCITY_1 = "target_velocity_1"
    TARGET_ACCELERATION_1 = "target_acceleration_1"
    TARGET_TORQUE_1 = "target_torque_1"
    COMPUTED_INERTIA_1 = "computed_inertia_1"
    COMPUTED_TORQUE_1 = "computed_torque_1"
    MOTOR_POSITION_1 = "motor_position_1"
    MOTOR_VELOCITY_1 = "motor_velocity_1"
    JOINT_POSITION_1 = "joint_position_1"
    JOINT_VELOCITY_1 = "joint_velocity_1"
    MOTOR_TORQUE_1 = "motor_torque_1"
    TORQUE_SENSOR_A_1 = "torque_sensor_a_1"
    TORQUE_SENSOR_B_1 = "torque_sensor_b_1"
    MOTOR_IQ_1 = "motor_iq_1"
    MOTOR_ID_1 = "motor_id_1"
    POWER_MOTOR_EL_1 = "power_motor_el_1"
    POWER_MOTOR_MECH_1 = "power_motor_mech_1"
    POWER_LOAD_MECH_1 = "power_load_mech_1"
    MOTOR_VOLTAGE_1 = "motor_voltage_1"
    SUPPLY_VOLTAGE_1 = "supply_voltage_1"
    BRAKE_VOLTAGE_1 = "brake_voltage_1"
    TARGET_POSITION_2 = "target_position_2"
    TARGET_VELOCITY_2 = "target_velocity_2"
    TARGET_ACCELERATION_2 = "target_acceleration_2"
    TARGET_TORQUE_2 = "target_torque_2"
    COMPUTED_INERTIA_2 = "computed_inertia_2"
    COMPUTED_TORQUE_2 = "computed_torque_2"
    MOTOR_POSITION_2 = "motor_position_2"
    MOTOR_VELOCITY_2 = "motor_velocity_2"
    JOINT_POSITION_2 = "joint_position_2"
    JOINT_VELOCITY_2 = "joint_velocity_2"
    MOTOR_TORQUE_2 = "motor_torque_2"
    TORQUE_SENSOR_A_2 = "torque_sensor_a_2"
    TORQUE_SENSOR_B_2 = "torque_sensor_b_2"
    MOTOR_IQ_2 = "motor_iq_2"
    MOTOR_ID_2 = "motor_id_2"
    POWER_MOTOR_EL_2 = "power_motor_el_2"
    POWER_MOTOR_MECH_2 = "power_motor_mech_2"
    POWER_LOAD_MECH_2 = "power_load_mech_2"
    MOTOR_VOLTAGE_2 = "motor_voltage_2"
    SUPPLY_VOLTAGE_2 = "supply_voltage_2"
    BRAKE_VOLTAGE_2 = "brake_voltage_2"
    TARGET_POSITION_3 = "target_position_3"
    TARGET_VELOCITY_3 = "target_velocity_3"
    TARGET_ACCELERATION_3 = "target_acceleration_3"
    TARGET_TORQUE_3 = "target_torque_3"
    COMPUTED_INERTIA_3 = "computed_inertia_3"
    COMPUTED_TORQUE_3 = "computed_torque_3"
    MOTOR_POSITION_3 = "motor_position_3"
    MOTOR_VELOCITY_3 = "motor_velocity_3"
    JOINT_POSITION_3 = "joint_position_3"
    JOINT_VELOCITY_3 = "joint_velocity_3"
    MOTOR_TORQUE_3 = "motor_torque_3"
    TORQUE_SENSOR_A_3 = "torque_sensor_a_3"
    TORQUE_SENSOR_B_3 = "torque_sensor_b_3"
    MOTOR_IQ_3 = "motor_iq_3"
    MOTOR_ID_3 = "motor_id_3"
    POWER_MOTOR_EL_3 = "power_motor_el_3"
    POWER_MOTOR_MECH_3 = "power_motor_mech_3"
    POWER_LOAD_MECH_3 = "power_load_mech_3"
    MOTOR_VOLTAGE_3 = "motor_voltage_3"
    SUPPLY_VOLTAGE_3 = "supply_voltage_3"
    BRAKE_VOLTAGE_3 = "brake_voltage_3"
    TARGET_POSITION_4 = "target_position_4"
    TARGET_VELOCITY_4 = "target_velocity_4"
    TARGET_ACCELERATION_4 = "target_acceleration_4"
    TARGET_TORQUE_4 = "target_torque_4"
    COMPUTED_INERTIA_4 = "computed_inertia_4"
    COMPUTED_TORQUE_4 = "computed_torque_4"
    MOTOR_POSITION_4 = "motor_position_4"
    MOTOR_VELOCITY_4 = "motor_velocity_4"
    JOINT_POSITION_4 = "joint_position_4"
    JOINT_VELOCITY_4 = "joint_velocity_4"
    MOTOR_TORQUE_4 = "motor_torque_4"
    TORQUE_SENSOR_A_4 = "torque_sensor_a_4"
    TORQUE_SENSOR_B_4 = "torque_sensor_b_4"
    MOTOR_IQ_4 = "motor_iq_4"
    MOTOR_ID_4 = "motor_id_4"
    POWER_MOTOR_EL_4 = "power_motor_el_4"
    POWER_MOTOR_MECH_4 = "power_motor_mech_4"
    POWER_LOAD_MECH_4 = "power_load_mech_4"
    MOTOR_VOLTAGE_4 = "motor_voltage_4"
    SUPPLY_VOLTAGE_4 = "supply_voltage_4"
    BRAKE_VOLTAGE_4 = "brake_voltage_4"
    TARGET_POSITION_5 = "target_position_5"
    TARGET_VELOCITY_5 = "target_velocity_5"
    TARGET_ACCELERATION_5 = "target_acceleration_5"
    TARGET_TORQUE_5 = "target_torque_5"
    COMPUTED_INERTIA_5 = "computed_inertia_5"
    COMPUTED_TORQUE_5 = "computed_torque_5"
    MOTOR_POSITION_5 = "motor_position_5"
    MOTOR_VELOCITY_5 = "motor_velocity_5"
    JOINT_POSITION_5 = "joint_position_5"
    JOINT_VELOCITY_5 = "joint_velocity_5"
    MOTOR_TORQUE_5 = "motor_torque_5"
    TORQUE_SENSOR_A_5 = "torque_sensor_a_5"
    TORQUE_SENSOR_B_5 = "torque_sensor_b_5"
    MOTOR_IQ_5 = "motor_iq_5"
    MOTOR_ID_5 = "motor_id_5"
    POWER_MOTOR_EL_5 = "power_motor_el_5"
    POWER_MOTOR_MECH_5 = "power_motor_mech_5"
    POWER_LOAD_MECH_5 = "power_load_mech_5"
    MOTOR_VOLTAGE_5 = "motor_voltage_5"
    SUPPLY_VOLTAGE_5 = "supply_voltage_5"
    BRAKE_VOLTAGE_5 = "brake_voltage_5"
    TARGET_POSITION_6 = "target_position_6"
    TARGET_VELOCITY_6 = "target_velocity_6"
    TARGET_ACCELERATION_6 = "target_acceleration_6"
    TARGET_TORQUE_6 = "target_torque_6"
    COMPUTED_INERTIA_6 = "computed_inertia_6"
    COMPUTED_TORQUE_6 = "computed_torque_6"
    MOTOR_POSITION_6 = "motor_position_6"
    MOTOR_VELOCITY_6 = "motor_velocity_6"
    JOINT_POSITION_6 = "joint_position_6"
    JOINT_VELOCITY_6 = "joint_velocity_6"
    MOTOR_TORQUE_6 = "motor_torque_6"
    TORQUE_SENSOR_A_6 = "torque_sensor_a_6"
    TORQUE_SENSOR_B_6 = "torque_sensor_b_6"
    MOTOR_IQ_6 = "motor_iq_6"
    MOTOR_ID_6 = "motor_id_6"
    POWER_MOTOR_EL_6 = "power_motor_el_6"
    POWER_MOTOR_MECH_6 = "power_motor_mech_6"
    POWER_LOAD_MECH_6 = "power_load_mech_6"
    MOTOR_VOLTAGE_6 = "motor_voltage_6"
    SUPPLY_VOLTAGE_6 = "supply_voltage_6"
    BRAKE_VOLTAGE_6 = "brake_voltage_6"

    @classmethod
    def all(cls) -> tuple[str, ...]:
        """Returns all signals (machine data and meta) included in the voraus-AD dataset.

        Returns:
            All signals of the voraus-AD dataset.
        """
        return (
            cls.TIME,
            cls.SAMPLE,
            cls.ANOMALY,
            cls.CATEGORY,
            cls.SETTING,
            cls.ACTION,
            cls.ACTIVE,
            cls.ROBOT_VOLTAGE,
            cls.ROBOT_CURRENT,
            cls.IO_CURRENT,
            cls.SYSTEM_CURRENT,
            cls.TARGET_POSITION_1,
            cls.TARGET_VELOCITY_1,
            cls.TARGET_ACCELERATION_1,
            cls.TARGET_TORQUE_1,
            cls.COMPUTED_INERTIA_1,
            cls.COMPUTED_TORQUE_1,
            cls.MOTOR_POSITION_1,
            cls.MOTOR_VELOCITY_1,
            cls.JOINT_POSITION_1,
            cls.JOINT_VELOCITY_1,
            cls.MOTOR_TORQUE_1,
            cls.TORQUE_SENSOR_A_1,
            cls.TORQUE_SENSOR_B_1,
            cls.MOTOR_IQ_1,
            cls.MOTOR_ID_1,
            cls.POWER_MOTOR_EL_1,
            cls.POWER_MOTOR_MECH_1,
            cls.POWER_LOAD_MECH_1,
            cls.MOTOR_VOLTAGE_1,
            cls.SUPPLY_VOLTAGE_1,
            cls.BRAKE_VOLTAGE_1,
            cls.TARGET_POSITION_2,
            cls.TARGET_VELOCITY_2,
            cls.TARGET_ACCELERATION_2,
            cls.TARGET_TORQUE_2,
            cls.COMPUTED_INERTIA_2,
            cls.COMPUTED_TORQUE_2,
            cls.MOTOR_POSITION_2,
            cls.MOTOR_VELOCITY_2,
            cls.JOINT_POSITION_2,
            cls.JOINT_VELOCITY_2,
            cls.MOTOR_TORQUE_2,
            cls.TORQUE_SENSOR_A_2,
            cls.TORQUE_SENSOR_B_2,
            cls.MOTOR_IQ_2,
            cls.MOTOR_ID_2,
            cls.POWER_MOTOR_EL_2,
            cls.POWER_MOTOR_MECH_2,
            cls.POWER_LOAD_MECH_2,
            cls.MOTOR_VOLTAGE_2,
            cls.SUPPLY_VOLTAGE_2,
            cls.BRAKE_VOLTAGE_2,
            cls.TARGET_POSITION_3,
            cls.TARGET_VELOCITY_3,
            cls.TARGET_ACCELERATION_3,
            cls.TARGET_TORQUE_3,
            cls.COMPUTED_INERTIA_3,
            cls.COMPUTED_TORQUE_3,
            cls.MOTOR_POSITION_3,
            cls.MOTOR_VELOCITY_3,
            cls.JOINT_POSITION_3,
            cls.JOINT_VELOCITY_3,
            cls.MOTOR_TORQUE_3,
            cls.TORQUE_SENSOR_A_3,
            cls.TORQUE_SENSOR_B_3,
            cls.MOTOR_IQ_3,
            cls.MOTOR_ID_3,
            cls.POWER_MOTOR_EL_3,
            cls.POWER_MOTOR_MECH_3,
            cls.POWER_LOAD_MECH_3,
            cls.MOTOR_VOLTAGE_3,
            cls.SUPPLY_VOLTAGE_3,
            cls.BRAKE_VOLTAGE_3,
            cls.TARGET_POSITION_4,
            cls.TARGET_VELOCITY_4,
            cls.TARGET_ACCELERATION_4,
            cls.TARGET_TORQUE_4,
            cls.COMPUTED_INERTIA_4,
            cls.COMPUTED_TORQUE_4,
            cls.MOTOR_POSITION_4,
            cls.MOTOR_VELOCITY_4,
            cls.JOINT_POSITION_4,
            cls.JOINT_VELOCITY_4,
            cls.MOTOR_TORQUE_4,
            cls.TORQUE_SENSOR_A_4,
            cls.TORQUE_SENSOR_B_4,
            cls.MOTOR_IQ_4,
            cls.MOTOR_ID_4,
            cls.POWER_MOTOR_EL_4,
            cls.POWER_MOTOR_MECH_4,
            cls.POWER_LOAD_MECH_4,
            cls.MOTOR_VOLTAGE_4,
            cls.SUPPLY_VOLTAGE_4,
            cls.BRAKE_VOLTAGE_4,
            cls.TARGET_POSITION_5,
            cls.TARGET_VELOCITY_5,
            cls.TARGET_ACCELERATION_5,
            cls.TARGET_TORQUE_5,
            cls.COMPUTED_INERTIA_5,
            cls.COMPUTED_TORQUE_5,
            cls.MOTOR_POSITION_5,
            cls.MOTOR_VELOCITY_5,
            cls.JOINT_POSITION_5,
            cls.JOINT_VELOCITY_5,
            cls.MOTOR_TORQUE_5,
            cls.TORQUE_SENSOR_A_5,
            cls.TORQUE_SENSOR_B_5,
            cls.MOTOR_IQ_5,
            cls.MOTOR_ID_5,
            cls.POWER_MOTOR_EL_5,
            cls.POWER_MOTOR_MECH_5,
            cls.POWER_LOAD_MECH_5,
            cls.MOTOR_VOLTAGE_5,
            cls.SUPPLY_VOLTAGE_5,
            cls.BRAKE_VOLTAGE_5,
            cls.TARGET_POSITION_6,
            cls.TARGET_VELOCITY_6,
            cls.TARGET_ACCELERATION_6,
            cls.TARGET_TORQUE_6,
            cls.COMPUTED_INERTIA_6,
            cls.COMPUTED_TORQUE_6,
            cls.MOTOR_POSITION_6,
            cls.MOTOR_VELOCITY_6,
            cls.JOINT_POSITION_6,
            cls.JOINT_VELOCITY_6,
            cls.MOTOR_TORQUE_6,
            cls.TORQUE_SENSOR_A_6,
            cls.TORQUE_SENSOR_B_6,
            cls.MOTOR_IQ_6,
            cls.MOTOR_ID_6,
            cls.POWER_MOTOR_EL_6,
            cls.POWER_MOTOR_MECH_6,
            cls.POWER_LOAD_MECH_6,
            cls.MOTOR_VOLTAGE_6,
            cls.SUPPLY_VOLTAGE_6,
            cls.BRAKE_VOLTAGE_6,
        )

    @classmethod
    def meta(cls) -> tuple[str, ...]:
        """Returns the meta colums of the voraus-AD dataset.

        Returns:
            The meta columns of the dataset.
        """
        return (
            cls.TIME,
            cls.SAMPLE,
            cls.ANOMALY,
            cls.CATEGORY,
            cls.SETTING,
            cls.ACTION,
            cls.ACTIVE,
        )

    @classmethod
    def meta_constant(cls) -> tuple[str, ...]:
        """Returns time invariant meta colums of the voraus-AD dataset.

        Returns:
            The time invariant meta columns.
        """
        return (
            cls.SAMPLE,
            cls.ANOMALY,
            cls.CATEGORY,
            cls.SETTING,
        )

    @classmethod
    def electrical(cls) -> tuple[str, ...]:
        """Returns the part of the machine data columns, which describes electrical values.

        Returns:
            The electrical signals.
        """
        return (
            cls.ROBOT_VOLTAGE,
            cls.ROBOT_CURRENT,
            cls.IO_CURRENT,
            cls.SYSTEM_CURRENT,
            cls.MOTOR_IQ_1,
            cls.MOTOR_ID_1,
            cls.POWER_MOTOR_EL_1,
            cls.MOTOR_VOLTAGE_1,
            cls.SUPPLY_VOLTAGE_1,
            cls.BRAKE_VOLTAGE_1,
            cls.MOTOR_IQ_2,
            cls.MOTOR_ID_2,
            cls.POWER_MOTOR_EL_2,
            cls.MOTOR_VOLTAGE_2,
            cls.SUPPLY_VOLTAGE_2,
            cls.BRAKE_VOLTAGE_2,
            cls.MOTOR_IQ_3,
            cls.MOTOR_ID_3,
            cls.POWER_MOTOR_EL_3,
            cls.MOTOR_VOLTAGE_3,
            cls.SUPPLY_VOLTAGE_3,
            cls.BRAKE_VOLTAGE_3,
            cls.MOTOR_IQ_4,
            cls.MOTOR_ID_4,
            cls.POWER_MOTOR_EL_4,
            cls.MOTOR_VOLTAGE_4,
            cls.SUPPLY_VOLTAGE_4,
            cls.BRAKE_VOLTAGE_4,
            cls.MOTOR_IQ_5,
            cls.MOTOR_ID_5,
            cls.POWER_MOTOR_EL_5,
            cls.MOTOR_VOLTAGE_5,
            cls.SUPPLY_VOLTAGE_5,
            cls.BRAKE_VOLTAGE_5,
            cls.MOTOR_IQ_6,
            cls.MOTOR_ID_6,
            cls.POWER_MOTOR_EL_6,
            cls.MOTOR_VOLTAGE_6,
            cls.SUPPLY_VOLTAGE_6,
            cls.BRAKE_VOLTAGE_6,
        )

    @classmethod
    def measured(cls) -> tuple[str, ...]:
        """Returns the part of the machine data, which describes measured values.

        Returns:
            The measured signals.
        """
        return (
            cls.ROBOT_VOLTAGE,
            cls.ROBOT_CURRENT,
            cls.IO_CURRENT,
            cls.SYSTEM_CURRENT,
            cls.MOTOR_POSITION_1,
            cls.MOTOR_VELOCITY_1,
            cls.JOINT_POSITION_1,
            cls.JOINT_VELOCITY_1,
            cls.TORQUE_SENSOR_A_1,
            cls.TORQUE_SENSOR_B_1,
            cls.MOTOR_VOLTAGE_1,
            cls.SUPPLY_VOLTAGE_1,
            cls.BRAKE_VOLTAGE_1,
            cls.MOTOR_POSITION_2,
            cls.MOTOR_VELOCITY_2,
            cls.JOINT_POSITION_2,
            cls.JOINT_VELOCITY_2,
            cls.TORQUE_SENSOR_A_2,
            cls.TORQUE_SENSOR_B_2,
            cls.MOTOR_VOLTAGE_2,
            cls.SUPPLY_VOLTAGE_2,
            cls.BRAKE_VOLTAGE_2,
            cls.MOTOR_POSITION_3,
            cls.MOTOR_VELOCITY_3,
            cls.JOINT_POSITION_3,
            cls.JOINT_VELOCITY_3,
            cls.TORQUE_SENSOR_A_3,
            cls.TORQUE_SENSOR_B_3,
            cls.MOTOR_VOLTAGE_3,
            cls.SUPPLY_VOLTAGE_3,
            cls.BRAKE_VOLTAGE_3,
            cls.MOTOR_POSITION_4,
            cls.MOTOR_VELOCITY_4,
            cls.JOINT_POSITION_4,
            cls.JOINT_VELOCITY_4,
            cls.TORQUE_SENSOR_A_4,
            cls.TORQUE_SENSOR_B_4,
            cls.MOTOR_VOLTAGE_4,
            cls.SUPPLY_VOLTAGE_4,
            cls.BRAKE_VOLTAGE_4,
            cls.MOTOR_POSITION_5,
            cls.MOTOR_VELOCITY_5,
            cls.JOINT_POSITION_5,
            cls.JOINT_VELOCITY_5,
            cls.TORQUE_SENSOR_A_5,
            cls.TORQUE_SENSOR_B_5,
            cls.MOTOR_VOLTAGE_5,
            cls.SUPPLY_VOLTAGE_5,
            cls.BRAKE_VOLTAGE_5,
            cls.MOTOR_POSITION_6,
            cls.MOTOR_VELOCITY_6,
            cls.JOINT_POSITION_6,
            cls.JOINT_VELOCITY_6,
            cls.TORQUE_SENSOR_A_6,
            cls.TORQUE_SENSOR_B_6,
            cls.MOTOR_VOLTAGE_6,
            cls.SUPPLY_VOLTAGE_6,
            cls.BRAKE_VOLTAGE_6,
        )

    @classmethod
    def robot(cls) -> tuple[str, ...]:
        """Returns all columns, which are not related to the robot axes, but to the robot itself.

        Returns:
            The robot system signals.
        """
        return (
            cls.ROBOT_VOLTAGE,
            cls.ROBOT_CURRENT,
            cls.IO_CURRENT,
            cls.SYSTEM_CURRENT,
        )

    @classmethod
    def machine(cls) -> tuple[str, ...]:
        """Returns all columns, which are machine data.

        This excludes the meta columns of the dataset.
        The machine data should be used for training, it contains all available measurements and target values.

        Returns:
            The machine data signals.
        """
        return tuple(s for s in cls.all() if s not in cls.meta())

    @classmethod
    def mechanical(cls) -> tuple[str, ...]:
        """Returns the columns, which describe mechanical values.

        Returns:
            The machanical signals.
        """
        return tuple(s for s in cls.machine() if s not in cls.electrical())

    @classmethod
    def computed(cls) -> tuple[str, ...]:
        """Returns the columns, which describe computed values like targets.

        Returns:
            The computed signals.
        """
        return tuple(s for s in cls.machine() if s not in cls.measured())

    @classmethod
    def axis(cls) -> tuple[str, ...]:
        """Returns the columns, which describe robot axis specific values.

        Returns:
            The robot axis specific signals.
        """
        signals_axis = tuple(s for s in cls.machine() if s not in cls.robot())
        number_of_axis = 6
        assert len(signals_axis) % number_of_axis == 0
        signals_per_axis = round(len(signals_axis) / number_of_axis)
        print(signals_per_axis)
        return signals_axis

    @classmethod
    def groups(cls) -> dict[str, tuple[str, ...]]:
        """Access the signal groups by name.

        Returns:
            The signal group dictionary.
        """
        return {
            "mechanical": cls.mechanical(),
            "electrical": cls.electrical(),
            "computed": cls.computed(),
            "measured": cls.measured(),
            "machine": cls.machine(),  #  all machine data
        }


class Category(IntEnum):
    """Describes the anomaly category as published in the paper."""

    AXIS_FRICTION = 0
    AXIS_WEIGHT = 1
    COLLISION_FOAM = 2
    COLLISION_CABLE = 3
    COLLISION_CARTON = 4
    MISS_CAN = 5
    LOSE_CAN = 6
    CAN_WEIGHT = 7
    ENTANGLED = 8
    INVALID_POSITION = 9
    MOTOR_COMMUTATION = 10
    WOBBLING_STATION = 11
    NORMAL_OPERATION = 12


class Variant(IntEnum):
    """Describes the anomaly variant as published in the paper."""

    A1_A = 0
    A1_B = 1
    A2_A = 2
    A2_B = 3
    A3_A = 4
    A3_B = 5
    A3_C = 6
    A4_A = 7
    A4_B = 8
    A4_C = 9
    A5_A = 10
    A5_B = 11
    A6_A = 12
    A6_B = 13
    A1_115G = 14
    A1_231G = 15
    A1_500G = 16
    A2_500G = 17
    A2_231G = 18
    A2_115G = 19
    A3_115G = 20
    A3_231G = 21
    A3_500G = 22
    A4_500G = 23
    A4_231G = 24
    A4_115G = 25
    A5_115G = 26
    A5_231G = 27
    A5_500G = 28
    A6_500G = 29
    A6_231G = 30
    A6_115G = 31
    LARGE_FULL = 32
    SMALL_FULL = 33
    SMALL_STRIPE = 34
    SMALL_HANGING_FULL = 35
    LARGE_HANGING_FULL = 36
    SMALL_HANGING_STRIPE = 37
    CONNECTOR_TOP = 38
    CONNECTOR_SIDE = 39
    LAN = 40
    STRIPE = 41
    FULL_A = 42
    FULL_B = 43
    CONVEYOR = 44
    NO_VACUUM = 45
    DEFECT_GRIPPER_DROP_CAN = 46
    DROP_1400MS = 47
    DROP_1100MS = 48
    DROP_100MS = 49
    DROP_200MS = 50
    LOSE_200MS = 51
    LOSE_300MS = 52
    LOSE_PLACE_100MS = 53
    DECREASE_95G = 54
    DECREASE_165G = 55
    EMPTY = 56
    INCREASE_242G = 57
    INCREASE_373G = 58
    INCREASE_407G = 59
    CABLE = 60
    PICK = 61
    A1_HIGH = 62
    A1_MEDIUM = 63
    A2_MEDIUM = 64
    A3_MEDIUM = 65
    A4_MEDIUM = 66
    A5_MEDIUM = 67
    A6_MEDIUM = 68
    LOW_DAMPING = 69
    MEDIUM_DAMPING = 70
    HIGH_DAMPING = 71
    PRE_A = 72
    PRE_B = 73
    BETWEEN_A = 74
    BETWEEN_B = 75
    BETWEEN_C = 76


class Action(IntEnum):
    """Describes the actual action of the robot as published in the paper."""

    VOID_1 = 0
    TO_SCAN_PTP = 1
    VOID_2 = 2
    OVER_OBJECT_PTP = 3
    VOID_3 = 4
    DOWN_PICK_LIN = 5
    VOID_4 = 6
    UP_PICK_LIN = 7
    VOID_5 = 8
    TO_PLACE_PTP = 9
    VOID_6 = 10
    DOWN_PLACE_LIN = 11
    VOID_7 = 12
    UP_PLACE_LIN = 13
    VOID_8 = 14


ANOMALY_CATEGORIES = [
    Category.AXIS_FRICTION,
    Category.AXIS_WEIGHT,
    Category.COLLISION_FOAM,
    Category.COLLISION_CABLE,
    Category.COLLISION_CARTON,
    Category.MISS_CAN,
    Category.LOSE_CAN,
    Category.CAN_WEIGHT,
    Category.ENTANGLED,
    Category.INVALID_POSITION,
    Category.MOTOR_COMMUTATION,
    Category.WOBBLING_STATION,
]

