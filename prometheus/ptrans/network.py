import pandas as pd
import random
from typing import Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum
from prometheus.car.car_output import CarOutputRoute

STOP_FILE_PATH = "data/gtfs/stops.txt"
TRAVEL_TIME_FILE_PATH = "data/gtfs/average_travel_times.csv"


class TransitType(Enum):
    """交通手段の種類を表す列挙型"""

    WALK = "walk"  # 徒歩
    BUS = "bus"  # バス
    COMBUS = "combus"  # コミュニティバス


@dataclass
class Node:
    """ネットワーク中のノードを表すクラス。"""

    name: str
    lat: float
    lon: float


@dataclass
class Edge:
    """ノード間のエッジを表すデータクラス"""

    travel_time: int  # 移動時間[分]
    transit_type: TransitType  # 交通手段の種類

@dataclass
class TimeTable:
    """時刻表を表すクラス。"""
    weekday: List[str] # 平日の時刻表
    holiday: List[str] # 休日の時刻表
    # TODO 名称は時刻表に入っているべきではないので分離する
    weekday_name: str # 平日の路線名称
    holiday_name: str # 休日の路線名称


@dataclass
class CombusEdge:
    org_node_id: str
    dst_node_id: str
    duration: int
    name: str
    shape: str
    time_tables: TimeTable


@dataclass
class CombusNode:
    id: str
    name: str
    lat: float
    lon: float


def convert_carroute_2_combus_data(
    car_output: CarOutputRoute,
) -> Tuple[List[CombusEdge], List[CombusNode]]:
    # 新しいノードIDを採番
    nodeid_list = []
    for _ in car_output.stops:
        new_nodeid = f"A{random.randint(1000, 9999)}"
        nodeid_list.append(new_nodeid)
    
    # エッジの追加
    combus_edges = []
    for i, section in enumerate(car_output.sections):
        org_nodeid = nodeid_list[i]
        dst_nodeid = (
            nodeid_list[i + 1] if i + 1 < len(nodeid_list) else nodeid_list[0]
        )
        # TODO 時刻表はsectionに入れるべき？
        time_table = TimeTable(
            weekday=car_output.stops[i].departure_times,
            holiday=car_output.stops[i].departure_times,
            weekday_name="コミュニティバス",
            holiday_name="コミュニティバス",
        )
        combus_edges.append(
            CombusEdge(
                org_node_id=org_nodeid,
                dst_node_id=dst_nodeid,
                duration=section.duration,
                name="コミュニティバス",
                shape=section.shape,
                time_tables=time_table,
            )
        )
    
    # ノードの追加
    combus_nodes = []
    for i, stop in enumerate(car_output.stops):
        combus_nodes.append(
            CombusNode(
                id=nodeid_list[i],
                name=f"バス停{i+1}",
                lat=stop.stop.coord.lat,
                lon=stop.stop.coord.lon,
            )
        )
    
    return combus_edges, combus_nodes


class Tracer:
    """経路確定後に時刻表を参照してトレースを行うクラス。"""

    def __init__(self) -> None:
        self.shape_dict: Dict[Tuple[str, str], str] = {}
        self.time_table_dict: Dict[Tuple[str, str], List[str]] = {}

    def add_combus_to_trace_data(self, combus: CarOutputRoute) -> None:
        pass


class Searcher:
    """経路探索を行い最適経路を求めるクラス。"""

    def __init__(self) -> None:
        self.node_dict: Dict[str, Node] = self._load_nodes(STOP_FILE_PATH)
        self.edge_dict: Dict[Tuple[str, str], Edge] = self._load_edges(
            TRAVEL_TIME_FILE_PATH
        )

    def _load_nodes(self, stops_file: str) -> Dict[str, Node]:
        stops_df = pd.read_csv(stops_file)
        node_dict: Dict[str, Node] = {}
        for _, row in stops_df.iterrows():
            node_dict[row["stop_id"]] = Node(
                name=row["stop_name"],
                lat=float(row["stop_lat"]),
                lon=float(row["stop_lon"]),
            )
        return node_dict

    def _load_edges(self, travel_time_file_path: str) -> Dict[Tuple[str, str], Edge]:
        travel_df = pd.read_csv(travel_time_file_path)
        edge_dict: Dict[Tuple[str, str], Edge] = {}
        for _, row in travel_df.iterrows():
            edge_dict[(row["stop_from"], row["stop_to"])] = Edge(
                travel_time=float(row["average_travel_time"]),
                transit_type=TransitType.BUS,
            )
        return edge_dict

    def add_combus_to_search_network(self, combus: CarOutputRoute):
        pass



if __name__ == "__main__":
    from prometheus.car.car_output import CarOutputRoute, CarOutputSection, CarOutputStop
    from prometheus.coord import Coord
    from prometheus.stop import Stop

    # 入力データを手動で構築
    car_output = CarOutputRoute(
        distance=26124,
        duration=44,
        sections=[
            CarOutputSection(
                distance=4331,
                duration=6,
                shape="avv~EgyfdYYk@e@}@Uc@iA`@e@b@y@v@{BoEU_@We@IO{CeGqDgH}FdA{AVg@J[FcDl@IBM@wA{Ci@gAgBwDsBqEIFw@n@kCSgAIiAIw@G_AESGOGGEyAM_EOkAGWCeBEq@AoAAmAEgACOA{@AG@aAEs@Aw@aCgBsFQPQNKRKQCm@y@MyASWEKEqB[mCa@iAQ}@O_Em@gDk@q@Go@B]AQCGCmCAaAAw@?G?M@I?Q?aC@}C@gB?eBKINMNQFYDc@@sDZW@m@E[Ce@D}@TgCb@OBaEx@Q@G}ACgAa@kC[kBKiA{AGC~@@VGHAp@"
            ),
            CarOutputSection(
                distance=6272,
                duration=9,
                shape="{||~Eg~hdYAd@CPMPWXa@d@g@t@GRoAfB{BmCgAaBw@mAGGEIDEdEaEJENMNOXPFBb@Nh@Ht@DlSHlFB?M?IhEBh@a@FsA@]jB]zAWfEw@r@MfB]FATmCRiCFo@LwAPqCTkCd@kG@_@@Y|Co^BOXeCLgBFgCFgDJcE@k@@g@BaCBqBFeEDqBBgC@_@?a@B_BBuBLiBPoCHiANoBBk@@MLkB?GBc@AK?{A?Q?]?WCoAAcAAi@@{@?QA]?K@_ABm@F_A@YPgBLuBB_@@OXsEX_F@W@OLgBBq@XyEFoABg@B[RcCZgDIE"
            ),
            CarOutputSection(
                distance=3252,
                duration=5,
                shape="_pz~EilsdYuC_B[c@kBeAaAYa@Iz@}AzAwCp@@tBBzAAj@?L?L?F?hABpDFb@?|@B~ABD?H?L?v@Bz@D\\@`@B`@JLBTHNH`@ThAv@pA~@tA|@VJb@J|ANpBLt@FTBL@R@P@nAHR@bGZJAPAVEPGZMbAc@bB{@`Ac@^KVEt@KTCdBOdB]`AYd@IX?^F^R~AjAB@|AjAvBzAb@\\XVfE|Ch@Al@?vA?dB?xA?`@@N@f@NxAn@lA`@l@NCkAxB_BDMLYt@}B\\}@Fi@Am@`Ce@`Ba@"
            ),
            CarOutputSection(
                distance=4439,
                duration=7,
                shape="_ev~EsvsdYhCq@KgBBo@Tm@d@oAY]HEt@o@r@{@k@iBw@eCfBiArBgAhGuCdAe@fBy@r@Yh@|BHf@?^FZH\\Zf@|@tA\\f@X`@f@Z^TLVHZBP@VETk@jDfAXLHJLPXn@tA^bADT@^OnAl@R^JdAZ|@XDFNF|@pJLnBNtBRF|@XXJ|Br@QfBEl@AJANGbA?d@?J@LDRDNB@?TCNq@vASd@@hFAlCObI[xGZ?`CBR?`D{B^BpARND\\ZVRPLnAp@r@`@xAz@tD~Ab@T~@b@vDnBdBz@jDlB`HvDcA`Fu@dF}BjRiCwA"
            ),
            CarOutputSection(
                distance=7830,
                duration=12,
                shape="uas~EexodYhCvAi@pEhD]hD_@x@In@GjAMz@IHAl@Gz@KHrAHnAHrAXlATfAHZDT@DF`@\\Gh@EO`Ec@|PM~FAj@d@bCBZBrA@`E?L?V@LFVLHTGRDDX@pBC\\ZTpALn@BbA?j@@HhBBj@V~H?HInDAL~AHRBFJb@RFxB@nAQ|CIjAD@H@MzAe@fGCb@Eb@IdAc@vFKrACbAArD?rB@`C?lC?\\?\\AdC?H?X?hB?vB?t@@lC?rFA~E?x@@h@Bj@Ff@Hj@lEbZhClR_GrAo@N}D`AwE`AmEbA`AfHm@P]M}@KyAUyAYg@KsAg@kB{@gAi@S@y@Y_DsAKEAHAHAF{@e@]MUAUDYP[J_@@iDa@_AC{ADc@?m@Nm@\\OPkAj@kBTuACy@K]AUBYLWTS^Kb@Ud@]b@y@j@OQMII?a@Es@Gy@F}Cr@eBf@{Bp@{Dv@eBVgGDsNAoG@UAg@?aAJ}@\\iDtALx@Db@A^I\\M\\WVeDxC"
            ),
        ],
        stops=[
            CarOutputStop(
                departure_times=[
                    "10:00", "10:44", "11:28", "12:12", "12:56",
                    "13:40", "14:24", "15:08", "15:52", "16:36"
                ],
                stay_time=1,
                stop=Stop(
                    coord=Coord(lat=36.65742, lon=137.17421),
                    name="バス停1"
                )
            ),
            CarOutputStop(
                departure_times=[
                    "10:06", "10:50", "11:34", "12:18", "13:02",
                    "13:46", "14:30", "15:14", "15:58", "16:42"
                ],
                stay_time=1,
                stop=Stop(
                    coord=Coord(lat=36.68936, lon=137.18519),
                    name="バス停2"
                )
            ),
            CarOutputStop(
                departure_times=[
                    "10:15", "10:59", "11:43", "12:27", "13:11",
                    "13:55", "14:39", "15:23", "16:07", "16:51"
                ],
                stay_time=1,
                stop=Stop(
                    coord=Coord(lat=36.67738, lon=137.23892),
                    name="バス停3"
                )
            ),
            CarOutputStop(
                departure_times=[
                    "10:20", "11:04", "11:48", "12:32", "13:16",
                    "14:00", "14:44", "15:28", "16:12", "16:56"
                ],
                stay_time=1,
                stop=Stop(
                    coord=Coord(lat=36.65493, lon=137.24001),
                    name="バス停4"
                )
            ),
            CarOutputStop(
                departure_times=[
                    "10:27", "11:11", "11:55", "12:39", "13:23",
                    "14:07", "14:51", "15:35", "16:19", "17:03"
                ],
                stay_time=1,
                stop=Stop(
                    coord=Coord(lat=36.63964, lon=137.21958),
                    name="バス停5"
                )
            ),
        ]
    )

    # テスト実行
    edges, nodes = convert_carroute_2_combus_data(car_output)
    print("CombusEdges:")
    for edge in edges:
        print(edge)
    print("CombusNodes:")
    for node in nodes:
        print(node)
