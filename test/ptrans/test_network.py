from prometheus.car.car_output import CarOutputRoute, CarOutputSection, CarOutputStop
from prometheus.coord import Coord
from prometheus.stop import Stop
from prometheus.ptrans.network import convert_car_route_2_combus_data
from prometheus.ptrans.network import CombusEdge, Node, TimeTable
from prometheus.ptrans.network import PtransSearcher
from prometheus.ptrans.network import SearchResult

car_output = CarOutputRoute(
    distance=26124,
    duration=44,
    sections=[
        CarOutputSection(
            distance=4331,
            duration=6,
            shape="avv~EgyfdYYk@e@}@Uc@iA`@e@b@y@v@{BoEU_@We@IO{CeGqDgH}FdA{AVg@J[FcDl@IBM@wA{Ci@gAgBwDsBqEIFw@n@kCSgAIiAIw@G_AESGOGGEyAM_EOkAGWCeBEq@AoAAmAEgACOA{@AG@aAEs@Aw@aCgBsFQPQNKRKQCm@y@MyASWEKEqB[mCa@iAQ}@O_Em@gDk@q@Go@B]AQCGCmCAaAAw@?G?M@I?Q?aC@}C@gB?eBKINMNQFYDc@@sDZW@m@E[Ce@D}@TgCb@OBaEx@Q@G}ACgAa@kC[kBKiA{AGC~@@VGHAp@",
        ),
        CarOutputSection(
            distance=6272,
            duration=9,
            shape="{||~Eg~hdYAd@CPMPWXa@d@g@t@GRoAfB{BmCgAaBw@mAGGEIDEdEaEJENMNOXPFBb@Nh@Ht@DlSHlFB?M?IhEBh@a@FsA@]jB]zAWfEw@r@MfB]FATmCRiCFo@LwAPqCTkCd@kG@_@@Y|Co^BOXeCLgBFgCFgDJcE@k@@g@BaCBqBFeEDqBBgC@_@?a@B_BBuBLiBPoCHiANoBBk@@MLkB?GBc@AK?{A?Q?]?WCoAAcAAi@@{@?QA]?K@_ABm@F_A@YPgBLuBB_@@OXsEX_F@W@OLgBBq@XyEFoABg@B[RcCZgDIE",
        ),
        CarOutputSection(
            distance=3252,
            duration=5,
            shape="_pz~EilsdYuC_B[c@kBeAaAYa@Iz@}AzAwCp@@tBBzAAj@?L?L?F?hABpDFb@?|@B~ABD?H?L?v@Bz@D\\@`@B`@JLBTHNH`@ThAv@pA~@tA|@VJb@J|ANpBLt@FTBL@R@P@nAHR@bGZJAPAVEPGZMbAc@bB{@`Ac@^KVEt@KTCdBOdB]`AYd@IX?^F^R~AjAB@|AjAvBzAb@\\XVfE|Ch@Al@?vA?dB?xA?`@@N@f@NxAn@lA`@l@NCkAxB_BDMLYt@}B\\}@Fi@Am@`Ce@`Ba@",
        ),
        CarOutputSection(
            distance=4439,
            duration=7,
            shape="_ev~EsvsdYhCq@KgBBo@Tm@d@oAY]HEt@o@r@{@k@iBw@eCfBiArBgAhGuCdAe@fBy@r@Yh@|BHf@?^FZH\\Zf@|@tA\\f@X`@f@Z^TLVHZBP@VETk@jDfAXLHJLPXn@tA^bADT@^OnAl@R^JdAZ|@XDFNF|@pJLnBNtBRF|@XXJ|Br@QfBEl@AJANGbA?d@?J@LDRDNB@?TCNq@vASd@@hFAlCObI[xGZ?`CBR?`D{B^BpARND\\ZVRPLnAp@r@`@xAz@tD~Ab@T~@b@vDnBdBz@jDlB`HvDcA`Fu@dF}BjRiCwA",
        ),
        CarOutputSection(
            distance=7830,
            duration=12,
            shape="uas~EexodYhCvAi@pEhD]hD_@x@In@GjAMz@IHAl@Gz@KHrAHnAHrAXlATfAHZDT@DF`@\\Gh@EO`Ec@|PM~FAj@d@bCBZBrA@`E?L?V@LFVLHTGRDDX@pBC\\ZTpALn@BbA?j@@HhBBj@V~H?HInDAL~AHRBFJb@RFxB@nAQ|CIjAD@H@MzAe@fGCb@Eb@IdAc@vFKrACbAArD?rB@`C?lC?\\?\\AdC?H?X?hB?vB?t@@lC?rFA~E?x@@h@Bj@Ff@Hj@lEbZhClR_GrAo@N}D`AwE`AmEbA`AfHm@P]M}@KyAUyAYg@KsAg@kB{@gAi@S@y@Y_DsAKEAHAHAF{@e@]MUAUDYP[J_@@iDa@_AC{ADc@?m@Nm@\\OPkAj@kBTuACy@K]AUBYLWTS^Kb@Ud@]b@y@j@OQMII?a@Es@Gy@F}Cr@eBf@{Bp@{Dv@eBVgGDsNAoG@UAg@?aAJ}@\\iDtALx@Db@A^I\\M\\WVeDxC",
        ),
    ],
    stops=[
        CarOutputStop(
            departure_times=[
                "10:00",
                "10:44",
                "11:28",
                "12:12",
                "12:56",
                "13:40",
                "14:24",
                "15:08",
                "15:52",
                "16:36",
            ],
            stay_time=1,
            stop=Stop(coord=Coord(lat=36.65742, lon=137.17421), name="バス停1"),
        ),
        CarOutputStop(
            departure_times=[
                "10:06",
                "10:50",
                "11:34",
                "12:18",
                "13:02",
                "13:46",
                "14:30",
                "15:14",
                "15:58",
                "16:42",
            ],
            stay_time=1,
            stop=Stop(coord=Coord(lat=36.68936, lon=137.18519), name="バス停2"),
        ),
        CarOutputStop(
            departure_times=[
                "10:15",
                "10:59",
                "11:43",
                "12:27",
                "13:11",
                "13:55",
                "14:39",
                "15:23",
                "16:07",
                "16:51",
            ],
            stay_time=1,
            stop=Stop(coord=Coord(lat=36.67738, lon=137.23892), name="バス停3"),
        ),
        CarOutputStop(
            departure_times=[
                "10:20",
                "11:04",
                "11:48",
                "12:32",
                "13:16",
                "14:00",
                "14:44",
                "15:28",
                "16:12",
                "16:56",
            ],
            stay_time=1,
            stop=Stop(coord=Coord(lat=36.65493, lon=137.24001), name="バス停4"),
        ),
        CarOutputStop(
            departure_times=[
                "10:27",
                "11:11",
                "11:55",
                "12:39",
                "13:23",
                "14:07",
                "14:51",
                "15:35",
                "16:19",
                "17:03",
            ],
            stay_time=1,
            stop=Stop(coord=Coord(lat=36.63964, lon=137.21958), name="バス停5"),
        ),
    ],
)


def test_convert_car_route_2_combus_data():
    edges, nodes = convert_car_route_2_combus_data(car_output)
    assert len(edges) == 5
    assert len(nodes) == 5

    expected_edges = [
        CombusEdge(
            org_node_id="A7311",
            dst_node_id="A7890",
            duration=6,
            name="コミュニティバス",
            shape="avv~EgyfdYYk@e@}@Uc@iA`@e@b@y@v@{BoEU_@We@IO{CeGqDgH}FdA{AVg@J[FcDl@IBM@wA{Ci@gAgBwDsBqEIFw@n@kCSgAIiAIw@G_AESGOGGEyAM_EOkAGWCeBEq@AoAAmAEgACOA{@AG@aAEs@Aw@aCgBsFQPQNKRKQCm@y@MyASWEKEqB[mCa@iAQ}@O_Em@gDk@q@Go@B]AQCGCmCAaAAw@?G?M@I?Q?aC@}C@gB?eBKINMNQFYDc@@sDZW@m@E[Ce@D}@TgCb@OBaEx@Q@G}ACgAa@kC[kBKiA{AGC~@@VGHAp@",
            time_tables=TimeTable(
                weekday=[
                    "10:00",
                    "10:44",
                    "11:28",
                    "12:12",
                    "12:56",
                    "13:40",
                    "14:24",
                    "15:08",
                    "15:52",
                    "16:36",
                ],
                holiday=[
                    "10:00",
                    "10:44",
                    "11:28",
                    "12:12",
                    "12:56",
                    "13:40",
                    "14:24",
                    "15:08",
                    "15:52",
                    "16:36",
                ],
                weekday_name="コミュニティバス",
                holiday_name="コミュニティバス",
            ),
        ),
        CombusEdge(
            org_node_id="A7890",
            dst_node_id="A1663",
            duration=9,
            name="コミュニティバス",
            shape="{||~Eg~hdYAd@CPMPWXa@d@g@t@GRoAfB{BmCgAaBw@mAGGEIDEdEaEJENMNOXPFBb@Nh@Ht@DlSHlFB?M?IhEBh@a@FsA@]jB]zAWfEw@r@MfB]FATmCRiCFo@LwAPqCTkCd@kG@_@@Y|Co^BOXeCLgBFgCFgDJcE@k@@g@BaCBqBFeEDqBBgC@_@?a@B_BBuBLiBPoCHiANoBBk@@MLkB?GBc@AK?{A?Q?]?WCoAAcAAi@@{@?QA]?K@_ABm@F_A@YPgBLuBB_@@OXsEX_F@W@OLgBBq@XyEFoABg@B[RcCZgDIE",
            time_tables=TimeTable(
                weekday=[
                    "10:06",
                    "10:50",
                    "11:34",
                    "12:18",
                    "13:02",
                    "13:46",
                    "14:30",
                    "15:14",
                    "15:58",
                    "16:42",
                ],
                holiday=[
                    "10:06",
                    "10:50",
                    "11:34",
                    "12:18",
                    "13:02",
                    "13:46",
                    "14:30",
                    "15:14",
                    "15:58",
                    "16:42",
                ],
                weekday_name="コミュニティバス",
                holiday_name="コミュニティバス",
            ),
        ),
        CombusEdge(
            org_node_id="A1663",
            dst_node_id="A5242",
            duration=5,
            name="コミュニティバス",
            shape="_pz~EilsdYuC_B[c@kBeAaAYa@Iz@}AzAwCp@@tBBzAAj@?L?L?F?hABpDFb@?|@B~ABD?H?L?v@Bz@D\\@`@B`@JLBTHNH`@ThAv@pA~@tA|@VJb@J|ANpBLt@FTBL@R@P@nAHR@bGZJAPAVEPGZMbAc@bB{@`Ac@^KVEt@KTCdBOdB]`AYd@IX?^F^R~AjAB@|AjAvBzAb@\\XVfE|Ch@Al@?vA?dB?xA?`@@N@f@NxAn@lA`@l@NCkAxB_BDMLYt@}B\\}@Fi@Am@`Ce@`Ba@",
            time_tables=TimeTable(
                weekday=[
                    "10:15",
                    "10:59",
                    "11:43",
                    "12:27",
                    "13:11",
                    "13:55",
                    "14:39",
                    "15:23",
                    "16:07",
                    "16:51",
                ],
                holiday=[
                    "10:15",
                    "10:59",
                    "11:43",
                    "12:27",
                    "13:11",
                    "13:55",
                    "14:39",
                    "15:23",
                    "16:07",
                    "16:51",
                ],
                weekday_name="コミュニティバス",
                holiday_name="コミュニティバス",
            ),
        ),
        CombusEdge(
            org_node_id="A5242",
            dst_node_id="A9376",
            duration=7,
            name="コミュニティバス",
            shape="_ev~EsvsdYhCq@KgBBo@Tm@d@oAY]HEt@o@r@{@k@iBw@eCfBiArBgAhGuCdAe@fBy@r@Yh@|BHf@?^FZH\\Zf@|@tA\\f@X`@f@Z^TLVHZBP@VETk@jDfAXLHJLPXn@tA^bADT@^OnAl@R^JdAZ|@XDFNF|@pJLnBNtBRF|@XXJ|Br@QfBEl@AJANGbA?d@?J@LDRDNB@?TCNq@vASd@@hFAlCObI[xGZ?`CBR?`D{B^BpARND\\ZVRPLnAp@r@`@xAz@tD~Ab@T~@b@vDnBdBz@jDlB`HvDcA`Fu@dF}BjRiCwA",
            time_tables=TimeTable(
                weekday=[
                    "10:20",
                    "11:04",
                    "11:48",
                    "12:32",
                    "13:16",
                    "14:00",
                    "14:44",
                    "15:28",
                    "16:12",
                    "16:56",
                ],
                holiday=[
                    "10:20",
                    "11:04",
                    "11:48",
                    "12:32",
                    "13:16",
                    "14:00",
                    "14:44",
                    "15:28",
                    "16:12",
                    "16:56",
                ],
                weekday_name="コミュニティバス",
                holiday_name="コミュニティバス",
            ),
        ),
        CombusEdge(
            org_node_id="A9376",
            dst_node_id="A7311",
            duration=12,
            name="コミュニティバス",
            shape="uas~EexodYhCvAi@pEhD]hD_@x@In@GjAMz@IHAl@Gz@KHrAHnAHrAXlATfAHZDT@DF`@\\Gh@EO`Ec@|PM~FAj@d@bCBZBrA@`E?L?V@LFVLHTGRDDX@pBC\\ZTpALn@BbA?j@@HhBBj@V~H?HInDAL~AHRBFJb@RFxB@nAQ|CIjAD@H@MzAe@fGCb@Eb@IdAc@vFKrACbAArD?rB@`C?lC?\\?\\AdC?H?X?hB?vB?t@@lC?rFA~E?x@@h@Bj@Ff@Hj@lEbZhClR_GrAo@N}D`AwE`AmEbA`AfHm@P]M}@KyAUyAYg@KsAg@kB{@gAi@S@y@Y_DsAKEAHAHAF{@e@]MUAUDYP[J_@@iDa@_AC{ADc@?m@Nm@\\OPkAj@kBTuACy@K]AUBYLWTS^Kb@Ud@]b@y@j@OQMII?a@Es@Gy@F}Cr@eBf@{Bp@{Dv@eBVgGDsNAoG@UAg@?aAJ}@\\iDtALx@Db@A^I\\M\\WVeDxC",
            time_tables=TimeTable(
                weekday=[
                    "10:27",
                    "11:11",
                    "11:55",
                    "12:39",
                    "13:23",
                    "14:07",
                    "14:51",
                    "15:35",
                    "16:19",
                    "17:03",
                ],
                holiday=[
                    "10:27",
                    "11:11",
                    "11:55",
                    "12:39",
                    "13:23",
                    "14:07",
                    "14:51",
                    "15:35",
                    "16:19",
                    "17:03",
                ],
                weekday_name="コミュニティバス",
                holiday_name="コミュニティバス",
            ),
        ),
    ]

    expected_nodes = [
        Node(node_id="A7311", name="バス停1", coord=Coord(lat=36.65742, lon=137.17421)),
        Node(node_id="A7890", name="バス停2", coord=Coord(lat=36.68936, lon=137.18519)),
        Node(node_id="A1663", name="バス停3", coord=Coord(lat=36.67738, lon=137.23892)),
        Node(node_id="A5242", name="バス停4", coord=Coord(lat=36.65493, lon=137.24001)),
        Node(node_id="A9376", name="バス停5", coord=Coord(lat=36.63964, lon=137.21958)),
    ]

    assert edges == expected_edges
    assert nodes == expected_nodes


def test_searcher_node_and_edge_dict():
    searcher = PtransSearcher()
    node_count = len(searcher.node_dict)
    edge_count = len(searcher.edge_dict)

    walk_edges = [
        e for e in searcher.edge_dict.values() if e.transit_type.name == "WALK"
    ]
    bus_edges = [e for e in searcher.edge_dict.values() if e.transit_type.name == "BUS"]

    assert len(walk_edges) > 0
    assert len(bus_edges) > 0


def test_add_combus_to_search_network():
    from prometheus.ptrans.network import (
        PtransSearcher,
        convert_car_route_2_combus_data,
        TransitType,
    )

    searcher = PtransSearcher()
    before_node_ids = set(searcher.node_dict.keys())
    before_edge_keys = set(searcher.edge_dict.keys())

    edges, nodes = convert_car_route_2_combus_data(car_output)
    searcher.add_combus_to_search_network(nodes, edges)

    after_node_ids = set(searcher.node_dict.keys())
    after_edge_keys = set(searcher.edge_dict.keys())
    added_node_ids = after_node_ids - before_node_ids
    added_edge_keys = after_edge_keys - before_edge_keys

    after_node_count = len(searcher.node_dict)
    before_node_count = len(before_node_ids)

    added_combus_edges = [
        k
        for k in added_edge_keys
        if getattr(searcher.edge_dict[k], "transit_type", None) == TransitType.COMBUS
    ]

    # 追加されたノードの数が期待通り
    assert after_node_count == before_node_count + len(nodes)

    # 追加されたノードのノード番号が「A」から始まる
    assert all(nid.startswith("A") for nid in added_node_ids)

    # 追加されたエッジの数が期待通り
    assert len(edges) == len(added_combus_edges)


def test_find_nearest_node():
    from prometheus.ptrans.network import haversine, EntryResult

    searcher = PtransSearcher()
    coord = Coord(lat=36.68936, lon=137.18519)
    entry_results = searcher.find_nearest_node(coord)
    assert len(entry_results) == 10

    # node_dictから全ノードとの距離を計算し、上位10件のノードIDを取得
    all_distances = {
        node_id: haversine(coord, node.coord)
        for node_id, node in searcher.node_dict.items()
    }
    expected_top10 = sorted(all_distances, key=all_distances.get)[:10]

    # EntryResultのnode.idが期待通りか確認
    result_ids = [entry.node.node_id for entry in entry_results]
    assert result_ids == expected_top10


def test_searcher_search():
    searcher = PtransSearcher()
    start = Coord(lat=36.689497, lon=137.183761)
    goal = Coord(lat=36.709989, lon=137.262297)
    start_candidates = searcher.find_nearest_node(start)
    goal_candidates = searcher.find_nearest_node(goal)
    result: SearchResult = searcher.search(start_candidates, goal_candidates)
    assert result is not None
    assert hasattr(result, "sections")
    assert len(result.sections) > 0


def test_tracer_loads():
    from prometheus.ptrans.network import PtransTracer

    tracer = PtransTracer()
    shape_count = len(tracer.shape_dict)
    time_table_count = len(tracer.time_table_dict)
    assert shape_count == 34978
    assert time_table_count == 35710


def test_add_combus_to_trace_data():
    from prometheus.ptrans.network import PtransTracer, convert_car_route_2_combus_data

    tracer = PtransTracer()
    before_shape_count = len(tracer.shape_dict)
    before_time_table_count = len(tracer.time_table_dict)

    combus_edges, combus_nodes = convert_car_route_2_combus_data(car_output)
    tracer.add_combus_to_trace_data(combus_edges)

    after_shape_count = len(tracer.shape_dict)
    after_time_table_count = len(tracer.time_table_dict)

    assert after_shape_count > before_shape_count
    assert after_time_table_count > before_time_table_count


def test_tracer_trace():
    from prometheus.ptrans.network import (
        PtransSearcher,
        PtransTracer,
        convert_car_route_2_combus_data,
    )

    # Searcherのセットアップ
    searcher = PtransSearcher()
    combus_edges, combus_nodes = convert_car_route_2_combus_data(car_output)
    searcher.add_combus_to_search_network(combus_nodes, combus_edges)

    # 経路探索
    start = Coord(lat=36.689497, lon=137.183761)
    goal = Coord(lat=36.709989, lon=137.262297)
    start_candidates = searcher.find_nearest_node(start)
    goal_candidates = searcher.find_nearest_node(goal)
    search_result = searcher.search(start_candidates, goal_candidates)

    # Tracerのセットアップ
    tracer = PtransTracer()
    tracer.set_node_dict(searcher.node_dict)
    start_time = "10:00"
    tracer.add_combus_to_trace_data(combus_edges)
    trace_output = tracer.trace(search_result, start_time, start, goal)

    # Section数のテスト
    assert len(trace_output.route.sections) == 5
    print(trace_output.route.sections)
