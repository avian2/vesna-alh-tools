<experimentDescription>
  <experimentAbstract>
    <title>2.4 GHz cognitive terminal simulation demo</title>
    <author>
      <name>Tomaž Šolc</name>
      <email>tomaz.solc@ijs.si</email>
      <address>Jamova cesta 39, Ljubljana,Slovenia</address>
      <phone>+386 1 477 3699</phone>
      <institution>Jožef Stefan Institute</institution>
    </author>
    <releaseDate>2013-05-22</releaseDate>
    <experimentSummary>Scripted simulation of a legacy terminal forcing a cognitive terminal to switch transmission channel.</experimentSummary>
    <relatedExperiments></relatedExperiments>
    <notes>Additional VESNA metadata follows:

      {
          "duration": 60, 
          "step_hz": 400000.0
      }
    </notes>
  </experimentAbstract>
  <metaInformation>
    <device>
      <name>Spectrum sensor 1</name>
      <description>Additional VESNA metadata follows:

        {
            "cluster_id": 10001, 
            "base_url": "https://crn.log-a-tec.eu/communicator", 
            "addr": 2
        }
      </description>
    </device>
    <device>
      <name>Spectrum sensor 2</name>
      <description>Additional VESNA metadata follows:

        {
            "cluster_id": 10001, 
            "base_url": "https://crn.log-a-tec.eu/communicator", 
            "addr": 6
        }
      </description>
    </device>
    <device>
      <name>Spectrum sensor 3</name>
      <description>Additional VESNA metadata follows:

        {
            "cluster_id": 10001, 
            "base_url": "https://crn.log-a-tec.eu/communicator", 
            "addr": 17 
        }
      </description>
    </device>
    <device>
      <name>Cognitive terminal</name>
      <description>Additional VESNA metadata follows:

        {
            "cluster_id": 10001, 
            "base_url": "https://crn.log-a-tec.eu/communicator", 
            "addr": 25
        }
      </description>
    </device>
    <device>
      <name>Legacy terminal</name>
      <description>Additional VESNA metadata follows:

        {
            "cluster_id": 10001, 
            "base_url": "https://crn.log-a-tec.eu/communicator", 
            "addr": 16
        }
      </description>
    </device>
    <location>
      <layout/>
      <mobility/>
    </location>
    <date>2013-05-22</date>
    <radioFrequency>
      <startFrequency>2400000000.0</startFrequency>
      <stopFrequency>2500000000.0</stopFrequency>
      <interferenceSources>Additional VESNA metadata follows:

        {
            "interferers": [
                {
                    "device": [
                        "https://crn.log-a-tec.eu/communicator", 
                        10001, 
                        25
                    ],
                    "programs": [
                      {
                        "power_dbm": 0, 
                        "center_hz": 2422000000.0,
                        "start_time": 5, 
                        "end_time": 30
                      },
                      {
                        "power_dbm": 0, 
                        "center_hz": 2445000000.0,
                        "start_time": 32, 
                        "end_time": 55
                      }
                    ]
                },
                {
                    "device": [
                        "https://crn.log-a-tec.eu/communicator", 
                        10001, 
                        16
                    ],
                    "programs": [
                      {
                        "power_dbm": 0, 
                        "center_hz": 2422800000.0,
                        "start_time": 25, 
                        "end_time": 55
                      }
                    ]
                }
            ]
        }
      </interferenceSources>
    </radioFrequency>
  </metaInformation>
</experimentDescription>
