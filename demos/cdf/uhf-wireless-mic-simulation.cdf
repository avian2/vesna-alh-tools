<experimentDescription>
  <experimentAbstract>
    <title>Secondary users and UHF microphone simulation demo</title>
    <author>
      <name>Tomaž Šolc</name>
      <email>tomaz.solc@ijs.si</email>
      <address>Jamova cesta 39, Ljubljana,Slovenia</address>
      <phone>+386 1 477 3699</phone>
      <institution>Jožef Stefan Institute</institution>
    </author>
    <releaseDate>2013-05-22</releaseDate>
    <experimentSummary>Scripted simulation of secondary users avoiding channels occupied by a wireless microphones.</experimentSummary>
    <relatedExperiments></relatedExperiments>
    <notes>Additional VESNA metadata follows:

      {
          "duration": 120, 
          "step_hz": 400000.0
      }
    </notes>
  </experimentAbstract>
  <metaInformation>
    <device>
      <name>Spectrum sensor</name>
      <description>Additional VESNA metadata follows:

        {
            "cluster_id": 10001, 
            "base_url": "https://crn.log-a-tec.eu/communicator", 
            "addr": 19
        }
      </description>
    </device>
    <device>
      <name>Secondary user 1</name>
      <description>Additional VESNA metadata follows:

        {
            "cluster_id": 10001, 
            "base_url": "https://crn.log-a-tec.eu/communicator", 
            "addr": 10
        }
      </description>
    </device>
    <device>
      <name>Secondary user 2</name>
      <description>Additional VESNA metadata follows:

        {
            "cluster_id": 10001, 
            "base_url": "https://crn.log-a-tec.eu/communicator", 
            "addr": 8
        }
      </description>
    </device>
    <device>
      <name>Wireless microphone</name>
      <description>Additional VESNA metadata follows:

        {
            "cluster_id": 10001, 
            "base_url": "https://crn.log-a-tec.eu/communicator", 
            "addr": 7
        }
      </description>
    </device>
    <location>
      <layout/>
      <mobility/>
    </location>
    <date>2013-05-22</date>
    <radioFrequency>
      <startFrequency>770000000.0</startFrequency>
      <stopFrequency>820000000.0</stopFrequency>
      <interferenceSources>Additional VESNA metadata follows:

        {
            "interferers": [
                {
                    "device": [
                        "https://crn.log-a-tec.eu/communicator", 
                        10001, 
                        7
                    ],
                    "programs": [
                      {
                        "power_dbm": 0, 
                        "center_hz": 790000000.0,
                        "start_time": 30,
                        "end_time": 70
                      },
                      {
                        "power_dbm": 0, 
                        "center_hz": 807000000.0,
                        "start_time": 80, 
                        "end_time": 120
                      }
                    ]
                },
                {
                    "device": [
                        "https://crn.log-a-tec.eu/communicator", 
                        10001, 
                        10
                    ],
                    "programs": [
                      {
                        "power_dbm": 0, 
                        "center_hz": 7870000000.0,
                        "start_time": 0, 
                        "end_time": 35 
                      },
                      {
                        "power_dbm": 0, 
                        "center_hz": 7800000000.0,
                        "start_time": 35, 
                        "end_time": 120 
                      }
                    ]
                },
                {
                    "device": [
                        "https://crn.log-a-tec.eu/communicator", 
                        10001, 
                        8
                    ],
                    "programs": [
                      {
                        "power_dbm": 0, 
                        "center_hz": 795000000.0,
                        "start_time": 0, 
                        "end_time": 35 
                      },
                      {
                        "power_dbm": 0, 
                        "center_hz": 800000000.0,
                        "start_time": 35, 
                        "end_time": 85
                      },
                      {
                        "power_dbm": 0, 
                        "center_hz": 800000000.0,
                        "start_time": 85,
                        "end_time": 120
                      }
                    ]
                }
            ]
        }
      </interferenceSources>
    </radioFrequency>
  </metaInformation>
</experimentDescription>
