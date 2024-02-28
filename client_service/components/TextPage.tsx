import { useEffect, useState } from 'react';
import axios from 'axios';

interface TextItem {
  id: number;
  title: string;
  description: string;
  fanfic_text: string;
  pic: string;
}

const TextPage = ({ id }) => {
  console.log(id)
  const [text, setText] = useState(null);

  useEffect(() => {
    const fetchText = async () => {
      try {
        const response = await axios.get(`http://localhost:8000/get_text/${id}`);
        setText(response.data);
      } catch (error) {
        console.error('Error fetching text:', error);
      }
    };

    fetchText();
  }, [id]);

  if (!text) {
    return <div>Loading...</div>;
  }

  return (
    <div>
      <h1>{text.title}</h1>
      <p>{text.description}</p>
      {/* Дополнительная информация о тексте */}
    </div>
  );
};

export default TextPage;

export async function getServerSideProps(context) {
  const { id } = context.query;

  return {
    props: {
      id,
    },
  };
}
