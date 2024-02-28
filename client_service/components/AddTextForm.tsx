import { useState } from 'react';
import {Button, TextInput, Text, Flex} from '@mantine/core';
import axios from 'axios';

const AddTextForm = () => {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    fanfic_text: '',
  });

  const handleChange = (e: { target: { name: any; value: any; }; }) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = (e: { preventDefault: () => void; }) => {
    e.preventDefault();
    axios.post('http://localhost:8000/create_text', formData)
      .then(response => {
        console.log('Text created:', response.data);
        // Дополнительные действия, например, обновление списка текстов
      })
      .catch(error => {
        console.error('Error creating text:', error);
      });
  };

  return (
    <Flex>
      <form onSubmit={handleSubmit}>
        <TextInput
          label="Title"
          name="title"
          value={formData.title}
          onChange={handleChange}
          required
        />
        <TextInput
          label="Description"
          name="description"
          value={formData.description}
          onChange={handleChange}
          required
        />
        <TextInput
          label="Fanfic Text"
          name="fanfic_text"
          value={formData.fanfic_text}
          onChange={handleChange}
          required
        />
        <Button type="submit">Add Text</Button>
      </form>
    </Flex>

  );
};

export default AddTextForm;