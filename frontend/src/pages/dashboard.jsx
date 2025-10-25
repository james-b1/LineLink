import { useEffect, useState } from "react";
import api from "../api/api.js";
import LineTable from "../components/LineTable";
import SystemHealthCard from "../components/SystemHealthCard";
import WeatherCard from "../components/WeatherCardTest";

const Dashboard = () => {
  const [data, setData] = useState(null);

  useEffect(() => {
    api
      .get("/current-conditions")
      .then((res) => setData(res.data))
      .catch((err) => console.error(err));
  }, []);

  if (!data) return <p>Loading...</p>;

  return (
    <div>
      <h1>LineLink Dashboard</h1>
      <WeatherCard weather={data.weather} />
      <SystemHealthCard health={data.system_health} />
      <LineTable lines={data.lines} />
    </div>
  );
};

export default Dashboard;
